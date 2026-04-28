"""
Advanced University Timetable Generator
Implements compact scheduling with strict subject/day constraints.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class ConstraintViolation(Exception):
    """Custom exception for constraint violations."""


class TimetableGenerator:
    """
    Timetable generator that prefers compact days but will use every
    available teaching slot when needed to complete student timetables.
    """

    def __init__(self, db):
        self.db = db
        self._reset_generation_state()

    def _reset_generation_state(self):
        self.classrooms = []
        self.subjects = []
        self.faculty = []
        self.student_groups = []
        self.timing_config = None

        self.faculty_schedule = defaultdict(set)
        self.classroom_schedule = defaultdict(set)
        self.student_schedule = defaultdict(set)
        self.faculty_entry_details = defaultdict(dict)
        self.classroom_entry_details = defaultdict(dict)
        self.faculty_hours = defaultdict(int)

        self.subject_priority = {}
        self.daily_slot_usage = defaultdict(lambda: defaultdict(set))
        self.generation_warnings = []

    async def generate(self, params):
        """Main generation method."""
        print("Starting advanced timetable generation...")
        self._reset_generation_state()

        await self._load_data()

        validation_result = await self._validate_data()
        if not validation_result["valid"]:
            return {
                "success": False,
                "errors": validation_result["errors"],
                "message": "Validation failed",
            }

        self._filter_data(params)
        self._prepare_subject_instances()

        try:
            self._calculate_subject_priorities()
            generated_timetables = await self._generate_timetables_smart()
            if not generated_timetables:
                return {
                    "success": False,
                    "error": "No valid timetable could be generated for the current data set",
                    "warnings": self.generation_warnings,
                    "message": "Could not generate conflict-free timetable",
                }
            await self._save_timetables(generated_timetables)
            return {
                "success": True,
                "message": "Timetables generated successfully with compact scheduling",
                "timetables_count": len(generated_timetables),
                "timetables": generated_timetables,
                "warnings": self.generation_warnings,
            }
        except ConstraintViolation as exc:
            return {
                "success": False,
                "error": str(exc),
                "warnings": self.generation_warnings,
                "message": "Could not generate conflict-free timetable",
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "warnings": self.generation_warnings,
                "message": "Timetable generation failed",
            }

    async def _load_data(self):
        self.classrooms = await self.db.classrooms.find({}).to_list(1000)
        self.subjects = await self.db.subjects.find({}).to_list(2000)
        self.faculty = await self.db.faculty.find({}).to_list(1000)
        self.student_groups = await self.db.student_groups.find({}).to_list(1000)
        self.timing_config = await self.db.timing_config.find_one({"config_id": "default"})

    async def _validate_data(self) -> Dict:
        errors = []

        if not self.timing_config:
            errors.append("Timing configuration not found. Configure working hours first.")
            return {"valid": False, "errors": errors}

        if not self.classrooms:
            errors.append("No classrooms defined")
        if not self.subjects:
            errors.append("No subjects defined")
        if not self.faculty:
            errors.append("No faculty defined")
        if not self.student_groups:
            errors.append("No student groups defined")

        if errors:
            return {"valid": False, "errors": errors}

        theory_classrooms = [c for c in self.classrooms if c.get("room_type") == "Theory"]
        practical_classrooms = [c for c in self.classrooms if c.get("room_type") == "Practical"]

        if not theory_classrooms:
            errors.append("No theory classrooms available")

        practical_subjects = [s for s in self.subjects if s.get("subject_type") == "Practical"]
        if practical_subjects and not practical_classrooms:
            errors.append(f"Found {len(practical_subjects)} practical subjects but no labs available")

        working_days = self.timing_config.get("working_days", [])
        if not working_days:
            errors.append("No working days configured")

        non_break_slots = [slot for slot in self.timing_config.get("time_slots", []) if not slot.get("is_break")]
        if not non_break_slots:
            errors.append("No teaching slots configured")

        return {"valid": len(errors) == 0, "errors": errors}

    def _filter_data(self, params):
        if params.branches:
            self.subjects = [s for s in self.subjects if s["branch"] in params.branches]
            self.student_groups = [g for g in self.student_groups if g["branch"] in params.branches]

        if params.semesters:
            self.subjects = [s for s in self.subjects if s["semester"] in params.semesters]
            self.student_groups = [g for g in self.student_groups if g["semester"] in params.semesters]

    def _prepare_subject_instances(self):
        """
        Create unique internal schedule keys.
        Some CSV rows reuse the same subject code, which breaks dict-based scheduling.
        """
        prepared_subjects = []
        seen = defaultdict(int)

        for subject in self.subjects:
            subject_copy = dict(subject)
            base_key = f"{subject_copy['branch']}|{subject_copy['semester']}|{subject_copy['subject_code']}"
            seen[base_key] += 1
            subject_copy["schedule_key"] = (
                base_key if seen[base_key] == 1 else f"{base_key}#{seen[base_key]}"
            )
            prepared_subjects.append(subject_copy)

        self.subjects = prepared_subjects

    def _calculate_subject_priorities(self):
        for subject in self.subjects:
            priority = 0

            if subject.get("subject_type") == "Practical":
                priority += 100
            if subject.get("priority") == "core":
                priority += 50

            priority += subject.get("credits", 0) * 10

            if subject.get("priority") == "elective":
                priority -= 30

            self.subject_priority[subject["schedule_key"]] = priority

    async def _generate_timetables_smart(self) -> List[Dict]:
        timetables = []
        student_timetables = []

        subject_groups = defaultdict(list)
        for subject in self.subjects:
            subject_groups[(subject["branch"], subject["semester"])].append(subject)

        for key in subject_groups:
            subject_groups[key].sort(
                key=lambda subject: self.subject_priority.get(subject["schedule_key"], 0),
                reverse=True,
            )

        for student_group in self.student_groups:
            branch = student_group["branch"]
            semester = student_group["semester"]
            group_id = student_group["group_id"]
            group_subjects = subject_groups.get((branch, semester), [])

            if not group_subjects:
                continue

            for division in student_group.get("divisions", []):
                division_id = f"{group_id}_{division['division_name']}"
                student_count = division["student_count"]

                try:
                    timetable = await self._generate_division_timetable_continuous(
                        division_id,
                        branch,
                        semester,
                        division["division_name"],
                        group_subjects,
                        student_count,
                    )
                    student_timetables.append(timetable)
                    self.generation_warnings.extend(timetable.get("warnings", []))
                except ConstraintViolation as exc:
                    self.generation_warnings.append(str(exc))

        timetables.extend(student_timetables)

        if not student_timetables:
            return timetables

        for fac in self.faculty:
            timetables.append(self._generate_faculty_timetable(fac["faculty_id"]))

        for classroom in self.classrooms:
            timetables.append(self._generate_classroom_timetable(classroom["classroom_id"]))

        return timetables

    async def _generate_division_timetable_continuous(
        self,
        division_id: str,
        branch: str,
        semester: int,
        division_name: str,
        subjects: List[Dict],
        student_count: int,
    ) -> Dict:
        entries = []
        working_days = self.timing_config["working_days"]
        time_slots = self.timing_config["time_slots"]

        for day in working_days:
            for slot in time_slots:
                entry_type = "break" if slot.get("is_break") else "empty"
                entries.append({"day": day, "slot_id": slot["slot_id"], "entry_type": entry_type})

        try:
            requirements = {subject["schedule_key"]: subject["credits"] for subject in subjects}
            self._validate_division_capacity(subjects, student_count, division_id, working_days, time_slots)

            scheduled_entries, unscheduled = self._schedule_continuous_smart(
                division_id,
                subjects,
                requirements,
                entries,
                working_days,
                time_slots,
                student_count,
            )
            warnings = []
            if unscheduled:
                warnings.append(
                    f"Unable to schedule all lectures for {division_id}: {', '.join(unscheduled[:12])}"
                )
        except ConstraintViolation as exc:
            scheduled_entries = entries
            warnings = [str(exc)]

        return self._build_student_timetable(
            division_id,
            branch,
            semester,
            division_name,
            scheduled_entries,
            warnings,
        )

    def _build_student_timetable(
        self,
        division_id: str,
        branch: str,
        semester: int,
        division_name: str,
        entries: List[Dict],
        warnings: List[str],
    ) -> Dict:
        return {
            "timetable_id": f"STUDENT_{division_id}",
            "entity_type": "student",
            "entity_id": division_id,
            "branch": branch,
            "semester": semester,
            "division": division_name,
            "entries": entries,
            "generation_status": "complete" if not warnings else "partial",
            "warnings": warnings,
            "generated_at": datetime.utcnow().isoformat(),
            "version": 1,
        }

    def _validate_division_capacity(
        self,
        subjects: List[Dict],
        student_count: int,
        division_id: str,
        working_days: List[str],
        time_slots: List[Dict],
    ):
        available_slots = len([slot for slot in time_slots if not slot.get("is_break")]) * len(working_days)
        required_slots = 0

        for subject in subjects:
            credits = subject["credits"]
            if subject["subject_type"] == "Practical":
                required_slots += credits * self.timing_config.get("practical_duration_slots", 2)
            else:
                required_slots += credits

        if required_slots > available_slots:
            raise ConstraintViolation(
                f"{division_id}: needs {required_slots} teaching slots but only {available_slots} are available"
            )

    def _schedule_continuous_smart(
        self,
        division_id: str,
        subjects: List[Dict],
        requirements: Dict,
        entries: List[Dict],
        working_days: List[str],
        time_slots: List[Dict],
        student_count: int,
    ) -> Tuple[List[Dict], List[str]]:
        slots_by_day = defaultdict(list)
        for day in working_days:
            for slot in time_slots:
                if not slot.get("is_break"):
                    slots_by_day[day].append(slot)

        scheduled_count = {key: 0 for key in requirements}
        subject_day_usage = defaultdict(set)

        practical_subjects = [subject for subject in subjects if subject["subject_type"] == "Practical"]
        theory_subjects = [subject for subject in subjects if subject["subject_type"] != "Practical"]

        for subject in practical_subjects:
            self._schedule_practical_continuous_smart(
                division_id,
                subject,
                entries,
                slots_by_day,
                student_count,
                requirements[subject["schedule_key"]],
                scheduled_count,
                subject_day_usage,
            )

        for subject in theory_subjects:
            self._schedule_theory_continuous_smart(
                division_id,
                subject,
                entries,
                slots_by_day,
                student_count,
                requirements[subject["schedule_key"]],
                scheduled_count,
                subject_day_usage,
            )

        unscheduled = []
        for subject in subjects:
            schedule_key = subject["schedule_key"]
            if scheduled_count[schedule_key] < requirements[schedule_key]:
                unscheduled.append(
                    f"{subject['subject_code']} ({requirements[schedule_key] - scheduled_count[schedule_key]} left)"
                )

        return entries, unscheduled

    def _schedule_theory_continuous_smart(
        self,
        division_id: str,
        subject: Dict,
        entries: List[Dict],
        slots_by_day: Dict,
        student_count: int,
        required_lectures: int,
        scheduled_count: Dict,
        subject_day_usage: Dict,
    ):
        subject_code = subject["subject_code"]
        subject_key = subject["schedule_key"]
        faculty_list = self._get_faculty_for_subject(subject_code)

        if not faculty_list:
            raise ConstraintViolation(f"No faculty assigned for subject {subject_code}")

        lectures_scheduled = 0
        days = list(slots_by_day.keys())

        while lectures_scheduled < required_lectures:
            placed = False
            for day in self._get_balanced_day_order(division_id, days):
                if day in subject_day_usage[subject_code]:
                    continue
                candidate_slots = self._get_available_candidate_slots(division_id, day, slots_by_day[day])
                for slot in candidate_slots:
                    faculty, classroom = self._select_theory_resources(
                        faculty_list, division_id, day, slot["slot_id"], student_count
                    )
                    if not faculty or not classroom:
                        continue

                    self._assign_lecture(
                        entries,
                        division_id,
                        day,
                        slot["slot_id"],
                        subject,
                        faculty,
                        classroom,
                        "theory",
                    )
                    self._mark_assignment(division_id, faculty, classroom, day, [slot["slot_id"]])

                    lectures_scheduled += 1
                    scheduled_count[subject_key] += 1
                    subject_day_usage[subject_code].add(day)
                    placed = True
                    break

                if placed:
                    break

            if not placed:
                break

    def _schedule_practical_continuous_smart(
        self,
        division_id: str,
        subject: Dict,
        entries: List[Dict],
        slots_by_day: Dict,
        student_count: int,
        required_sessions: int,
        scheduled_count: Dict,
        subject_day_usage: Dict,
    ):
        subject_code = subject["subject_code"]
        subject_key = subject["schedule_key"]
        faculty_list = self._get_faculty_for_subject(subject_code)

        if not faculty_list:
            raise ConstraintViolation(f"No faculty assigned for subject {subject_code}")

        practical_duration = self.timing_config.get("practical_duration_slots", 2)
        batch_size = subject.get("lab_batch_size") or student_count
        effective_lab_size = min(student_count, batch_size)
        total_sessions_needed = required_sessions
        sessions_scheduled = 0

        while sessions_scheduled < total_sessions_needed:
            placed = False
            for day in self._get_balanced_day_order(division_id, list(slots_by_day.keys())):
                if day in subject_day_usage[subject_code]:
                    continue
                for continuous_slots in self._get_available_day_blocks(
                    division_id, day, slots_by_day[day], practical_duration
                ):
                    slot_ids = [slot["slot_id"] for slot in continuous_slots]
                    faculty, classroom = self._select_practical_resources(
                        faculty_list, division_id, day, slot_ids, effective_lab_size
                    )
                    if not faculty or not classroom:
                        continue

                    for slot in continuous_slots:
                        self._assign_lecture(
                            entries,
                            division_id,
                            day,
                            slot["slot_id"],
                            subject,
                            faculty,
                            classroom,
                            "practical",
                            None,
                        )

                    self._mark_assignment(division_id, faculty, classroom, day, slot_ids)
                    sessions_scheduled += 1
                    scheduled_count[subject_key] += 1
                    subject_day_usage[subject_code].add(day)
                    placed = True
                    break

                if placed:
                    break

            if not placed:
                break

    def _select_theory_resources(
        self,
        faculty_list: List[Dict],
        division_id: str,
        day: str,
        slot_id: str,
        student_count: int,
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        for relax_preferences, relax_max_hours in ((False, False), (True, False), (True, True)):
            for faculty in sorted(faculty_list, key=lambda item: self.faculty_hours[item["faculty_id"]]):
                if not self._check_theory_constraints(
                    faculty["faculty_id"],
                    division_id,
                    day,
                    slot_id,
                    student_count,
                    faculty,
                    relax_preferences=relax_preferences,
                    relax_max_hours=relax_max_hours,
                ):
                    continue

                classroom = self._find_theory_classroom(day, slot_id, student_count)
                if classroom:
                    return faculty, classroom

        return None, None

    def _select_practical_resources(
        self,
        faculty_list: List[Dict],
        division_id: str,
        day: str,
        slot_ids: List[str],
        student_count: int,
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        for relax_preferences, relax_max_hours in ((False, False), (True, False), (True, True)):
            for faculty in sorted(faculty_list, key=lambda item: self.faculty_hours[item["faculty_id"]]):
                if not all(
                    self._check_practical_constraints(
                        faculty["faculty_id"],
                        division_id,
                        day,
                        slot_id,
                        faculty,
                        relax_preferences=relax_preferences,
                        relax_max_hours=relax_max_hours,
                    )
                    for slot_id in slot_ids
                ):
                    continue

                classroom = self._find_practical_classroom(day, slot_ids, student_count)
                if classroom:
                    return faculty, classroom

        return None, None

    def _mark_assignment(self, division_id: str, faculty: Dict, classroom: Dict, day: str, slot_ids: List[str]):
        faculty_id = faculty["faculty_id"]
        classroom_id = classroom["classroom_id"]

        for slot_id in slot_ids:
            self.faculty_schedule[faculty_id].add((day, slot_id))
            self.classroom_schedule[classroom_id].add((day, slot_id))
            self.student_schedule[division_id].add((day, slot_id))
            self.daily_slot_usage[division_id][day].add(slot_id)
            self.faculty_hours[faculty_id] += 1

    def _get_balanced_day_order(
        self,
        division_id: str,
        days: List[str],
    ) -> List[str]:
        def day_score(day: str) -> int:
            return len(self.daily_slot_usage[division_id][day])

        return sorted(days, key=day_score)

    def _get_available_candidate_slots(self, division_id: str, day: str, day_slots: List[Dict]) -> List[Dict]:
        used_slot_ids = self.daily_slot_usage[division_id][day]
        return [slot for slot in day_slots if slot["slot_id"] not in used_slot_ids]

    def _get_available_day_blocks(
        self,
        division_id: str,
        day: str,
        day_slots: List[Dict],
        block_size: int,
    ) -> List[List[Dict]]:
        used_slot_ids = self.daily_slot_usage[division_id][day]
        candidates = []
        for start_index in range(0, len(day_slots) - block_size + 1):
            candidate = day_slots[start_index : start_index + block_size]
            if not self._are_slots_continuous(candidate):
                continue
            if any(slot["slot_id"] in used_slot_ids for slot in candidate):
                continue
            candidates.append(candidate)
        return candidates

    def _check_theory_constraints(
        self,
        faculty_id: str,
        division_id: str,
        day: str,
        slot_id: str,
        student_count: int,
        faculty: Dict,
        relax_preferences: bool = False,
        relax_max_hours: bool = False,
    ) -> bool:
        if (day, slot_id) in self.faculty_schedule[faculty_id]:
            return False

        if (day, slot_id) in self.student_schedule[division_id]:
            return False

        max_hours = faculty.get("max_hours_per_week")
        if not relax_max_hours and max_hours is not None and self.faculty_hours[faculty_id] >= max_hours:
            return False

        preferred_time = faculty.get("preferred_time", "any")
        if not relax_preferences and preferred_time != "any":
            slot = self._get_slot_by_id(slot_id)
            if slot:
                hour = int(slot["start_time"].split(":")[0])
                if preferred_time == "morning" and hour >= 13:
                    return False
                if preferred_time == "afternoon" and hour < 13:
                    return False

        unavailable_days = faculty.get("unavailable_days", [])
        if day in unavailable_days:
            return False

        return True

    def _check_practical_constraints(
        self,
        faculty_id: str,
        division_id: str,
        day: str,
        slot_id: str,
        faculty: Dict,
        relax_preferences: bool = False,
        relax_max_hours: bool = False,
    ) -> bool:
        return self._check_theory_constraints(
            faculty_id,
            division_id,
            day,
            slot_id,
            0,
            faculty,
            relax_preferences=relax_preferences,
            relax_max_hours=relax_max_hours,
        )

    def _find_theory_classroom(self, day: str, slot_id: str, student_count: int) -> Optional[Dict]:
        theory_rooms = [room for room in self.classrooms if room["room_type"] == "Theory"]
        suitable_rooms = [room for room in theory_rooms if room["capacity"] >= student_count]
        suitable_rooms.sort(key=lambda room: room["capacity"])

        for room in suitable_rooms:
            if (day, slot_id) not in self.classroom_schedule[room["classroom_id"]]:
                return room

        return None

    def _find_practical_classroom(
        self,
        day: str,
        slot_ids: List[str],
        student_count: int,
    ) -> Optional[Dict]:
        practical_rooms = [room for room in self.classrooms if room["room_type"] == "Practical"]
        suitable_rooms = [room for room in practical_rooms if room["capacity"] >= student_count]
        suitable_rooms.sort(key=lambda room: room["capacity"])

        for room in suitable_rooms:
            if all((day, slot_id) not in self.classroom_schedule[room["classroom_id"]] for slot_id in slot_ids):
                return room

        return None

    def _assign_lecture(
        self,
        entries: List[Dict],
        division_id: str,
        day: str,
        slot_id: str,
        subject: Dict,
        faculty: Dict,
        classroom: Dict,
        entry_type: str,
        batch: str = None,
    ):
        for entry in entries:
            if entry["day"] == day and entry["slot_id"] == slot_id:
                entry["subject_code"] = subject["subject_code"]
                entry["subject_name"] = subject["subject_name"]
                entry["faculty_id"] = faculty["faculty_id"]
                entry["faculty_name"] = faculty["name"]
                entry["classroom_id"] = classroom["classroom_id"]
                entry["entry_type"] = entry_type
                if batch:
                    entry["batch"] = batch
                break

        detail_entry = {
            "day": day,
            "slot_id": slot_id,
            "subject_code": subject["subject_code"],
            "subject_name": subject["subject_name"],
            "faculty_id": faculty["faculty_id"],
            "faculty_name": faculty["name"],
            "classroom_id": classroom["classroom_id"],
            "entry_type": entry_type,
        }

        if batch:
            detail_entry["batch"] = batch

        self._store_entity_entry(self.faculty_entry_details[faculty["faculty_id"]], day, slot_id, detail_entry)
        self._store_entity_entry(
            self.classroom_entry_details[classroom["classroom_id"]], day, slot_id, detail_entry
        )

    def _store_entity_entry(self, entity_entries: Dict, day: str, slot_id: str, detail_entry: Dict):
        key = (day, slot_id)
        existing_entry = entity_entries.get(key)

        if not existing_entry:
            entity_entries[key] = detail_entry.copy()
            return

        existing_batch = existing_entry.get("batch")
        new_batch = detail_entry.get("batch")
        if existing_batch and new_batch and existing_batch != new_batch:
            existing_entry["batch"] = f"{existing_batch}, {new_batch}"
        elif not existing_batch and new_batch:
            existing_entry["batch"] = new_batch

    def _get_faculty_for_subject(self, subject_code: str) -> List[Dict]:
        exact_match = [faculty for faculty in self.faculty if subject_code in faculty.get("subjects", [])]
        if exact_match:
            return exact_match

        fallback_codes = self._subject_code_fallbacks(subject_code)
        return [
            faculty
            for faculty in self.faculty
            if any(code in faculty.get("subjects", []) for code in fallback_codes)
        ]

    def _subject_code_fallbacks(self, subject_code: str) -> List[str]:
        if subject_code.endswith("P"):
            return [subject_code[:-1] + "T"]
        if subject_code.endswith("T"):
            return [subject_code[:-1] + "P"]
        return []

    def _get_slot_by_id(self, slot_id: str) -> Optional[Dict]:
        for slot in self.timing_config.get("time_slots", []):
            if slot["slot_id"] == slot_id:
                return slot
        return None

    def _are_slots_continuous(self, slots: List[Dict]) -> bool:
        if len(slots) <= 1:
            return True

        sorted_slots = sorted(slots, key=lambda slot: slot["start_time"])
        for index in range(len(sorted_slots) - 1):
            if sorted_slots[index]["end_time"] != sorted_slots[index + 1]["start_time"]:
                return False
        return True

    def _generate_faculty_timetable(self, faculty_id: str) -> Dict:
        entries = []
        working_days = self.timing_config["working_days"]
        time_slots = self.timing_config["time_slots"]
        faculty_entries = self.faculty_entry_details.get(faculty_id, {})

        for day in working_days:
            for slot in time_slots:
                if slot.get("is_break"):
                    entries.append({"day": day, "slot_id": slot["slot_id"], "entry_type": "break"})
                elif (day, slot["slot_id"]) in faculty_entries:
                    entries.append(faculty_entries[(day, slot["slot_id"])].copy())
                else:
                    entries.append({"day": day, "slot_id": slot["slot_id"], "entry_type": "free"})

        faculty_info = next((faculty for faculty in self.faculty if faculty["faculty_id"] == faculty_id), None)
        return {
            "timetable_id": f"FACULTY_{faculty_id}",
            "entity_type": "faculty",
            "entity_id": faculty_id,
            "faculty_name": faculty_info["name"] if faculty_info else "",
            "entries": entries,
            "generated_at": datetime.utcnow().isoformat(),
            "version": 1,
        }

    def _generate_classroom_timetable(self, classroom_id: str) -> Dict:
        entries = []
        working_days = self.timing_config["working_days"]
        time_slots = self.timing_config["time_slots"]
        classroom_entries = self.classroom_entry_details.get(classroom_id, {})

        for day in working_days:
            for slot in time_slots:
                if slot.get("is_break"):
                    entries.append({"day": day, "slot_id": slot["slot_id"], "entry_type": "break"})
                elif (day, slot["slot_id"]) in classroom_entries:
                    entries.append(classroom_entries[(day, slot["slot_id"])].copy())
                else:
                    entries.append({"day": day, "slot_id": slot["slot_id"], "entry_type": "free"})

        classroom_info = next((room for room in self.classrooms if room["classroom_id"] == classroom_id), None)
        return {
            "timetable_id": f"CLASSROOM_{classroom_id}",
            "entity_type": "classroom",
            "entity_id": classroom_id,
            "classroom_name": classroom_id,
            "capacity": classroom_info["capacity"] if classroom_info else 0,
            "entries": entries,
            "generated_at": datetime.utcnow().isoformat(),
            "version": 1,
        }

    async def _save_timetables(self, timetables: List[Dict]):
        if not timetables:
            return

        await self.db.timetables.delete_many({})
        await self.db.timetables.insert_many(timetables)

        print(f"Saved {len(timetables)} timetables to database")
