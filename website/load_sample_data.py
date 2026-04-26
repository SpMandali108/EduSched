"""CSV loader for timetable module (Flask/PyMongo version)."""

import csv
from collections import defaultdict
from pathlib import Path


def _read_classrooms_csv(filepath):
    classrooms = []
    with open(filepath, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            room_type = row["type"].strip().lower()
            is_lab = "lab" in room_type
            classrooms.append(
                {
                    "classroom_id": row["room_id"].strip(),
                    "capacity": int(row["capacity"]),
                    "room_type": "Practical" if is_lab else "Theory",
                    "is_smart_classroom": int(row["capacity"]) >= 80,
                    "lab_type": "Computer Lab" if is_lab else None,
                }
            )
    return classrooms


def _read_faculty_csv(filepath):
    faculty_list = []
    with open(filepath, "r", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            faculty_id = row.get("faculty_id", "").strip()
            name = row.get("name", "").strip()
            if not faculty_id or not name:
                continue
            raw_subjects = row.get("subjects", "")
            if raw_subjects:
                subjects = [s.strip() for s in raw_subjects.strip().strip('"').split(",") if s.strip()]
            else:
                preferences = row.get("subject_preferences", "")
                subjects = [s.strip() for s in preferences.split(";") if s.strip()]
            raw_hours = row.get("max_hours_per_week", "").strip()
            max_hours = int(raw_hours) if raw_hours.isdigit() else 18
            digits = "".join(filter(str.isdigit, faculty_id))
            faculty_num = int(digits) if digits else 0
            preferred_time = "morning" if faculty_num % 3 == 0 else ("afternoon" if faculty_num % 3 == 1 else "any")
            faculty_list.append(
                {
                    "faculty_id": faculty_id,
                    "name": name,
                    "subjects": subjects,
                    "max_hours_per_week": max_hours,
                    "preferred_time": preferred_time,
                    "unavailable_days": [],
                }
            )
    return faculty_list


def _read_subjects_csv(filepath):
    subjects = []
    with open(filepath, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            subject_id = row["subject_id"].strip()
            # FIX: Normalise type — "lab" must be treated identically to
            # "practical" so the generator assigns lab rooms correctly.
            raw_type = row["type"].strip().lower()
            is_practical = subject_id.endswith("P") or raw_type in ("practical", "lab")
            subjects.append(
                {
                    "subject_code": subject_id,
                    "subject_name": row["subject_name"].strip(),
                    "branch": row["branch"].strip(),
                    "semester": int(row["sem"]),
                    "subject_type": "Practical" if is_practical else "Theory",
                    "credits": int(row["credits"]),
                    "priority": "core",
                    "requires_lab": is_practical,
                    "lab_batch_size": 30 if is_practical else None,
                }
            )
    return subjects


def _read_semester_aware_subjects(subjects_path, course_subject_map_path):
    base_subjects = {}
    with open(subjects_path, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            base_subjects[row["subject_id"].strip()] = row

    course_branch = {
        "CSE_UG": "CSE_UG",
        "CSE_PG": "CSE_PG",
        "ECE_UG": "ECE_UG",
        "ECE_PG": "ECE_PG",
    }

    subjects = []
    with open(course_subject_map_path, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            subject_id = row["subject_id"].strip()
            base = base_subjects.get(subject_id)
            if not base:
                continue
            course_id = row["course_id"].strip()
            branch = course_branch.get(course_id, course_id)
            sem = int(row["semester"])
            # FIX: Normalise type — treat "lab" as practical consistently.
            raw_type = base["type"].strip().lower()
            is_practical = subject_id.endswith("P") or raw_type in ("practical", "lab")
            subjects.append(
                {
                    "subject_code": subject_id,
                    "subject_name": base["subject_name"].strip(),
                    "branch": branch,
                    "semester": sem,
                    "subject_type": "Practical" if is_practical else "Theory",
                    "credits": int(base["credits"]),
                    "priority": "core",
                    "requires_lab": is_practical,
                    "lab_batch_size": 30 if is_practical else None,
                }
            )
    return subjects


def _read_students_csv(filepath):
    groups = defaultdict(lambda: {"branch": "", "semester": 0, "divisions": []})
    with open(filepath, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            branch = row.get("Branch", row.get("course_id", "")).strip()
            branch = branch if "_" in branch else f"{branch}_UG"
            semester = int(row["semester"])
            key = f"{branch}_SEM{semester}"
            groups[key]["branch"] = branch
            groups[key]["semester"] = semester
            groups[key]["divisions"].append(
                {"division_name": row["division"].strip(), "student_count": int(row["students"])}
            )
    return [
        {"group_id": key, "branch": value["branch"], "semester": value["semester"], "divisions": value["divisions"]}
        for key, value in groups.items()
    ]


def _read_faculty_limits(filepath):
    details = {}
    with open(filepath, "r", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            faculty_id = row.get("faculty_id", "").strip()
            if not faculty_id:
                continue
            raw_hours = row.get("max_hours_per_week", "").strip()
            details[faculty_id] = {
                "name": row.get("name", "").strip() or faculty_id,
                "max_hours_per_week": int(raw_hours) if raw_hours.isdigit() else 18,
            }
    return details


def _default_timing_config():
    """
    Default weekly timing configuration.

    Six non-break teaching slots per day across 5 days = 30 available slots.
    practical_duration_slots=2 means practicals occupy two consecutive slots
    (e.g. S1+S2, S4+S5, or S7+S8).  The generator's _are_slots_continuous()
    check requires back-to-back end_time/start_time matches — all three pairs
    satisfy this in the schedule below.
    """
    return {
        "config_id": "default",
        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_slots": [
            {"slot_id": "S1", "start_time": "09:00", "end_time": "10:00", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S2", "start_time": "10:00", "end_time": "11:00", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S3", "start_time": "11:00", "end_time": "11:15", "is_break": True,  "slot_type": "break"},
            {"slot_id": "S4", "start_time": "11:15", "end_time": "12:15", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S5", "start_time": "12:15", "end_time": "13:15", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S6", "start_time": "13:15", "end_time": "14:00", "is_break": True,  "slot_type": "break"},
            {"slot_id": "S7", "start_time": "14:00", "end_time": "15:00", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S8", "start_time": "15:00", "end_time": "16:00", "is_break": False, "slot_type": "theory"},
        ],
        "theory_duration_minutes": 60,
        # Each practical session occupies 2 consecutive non-break slots (2 hrs).
        "practical_duration_slots": 2,
    }


def load_sample_data(db, csv_root):
    base = Path(csv_root)
    classrooms = _read_classrooms_csv(base / "classrooms.csv")
    faculty = _read_faculty_csv(base / "faculty.csv")
    subjects = _read_semester_aware_subjects(base / "subjects.csv", base / "course_subject_map.csv")
    student_groups = _read_students_csv(base / "divisions.csv")

    db.classrooms.delete_many({})
    db.subjects.delete_many({})
    db.faculty.delete_many({})
    db.student_groups.delete_many({})
    db.timing_config.delete_many({})
    db.timetables.delete_many({})

    if classrooms:
        db.classrooms.insert_many(classrooms)
    if subjects:
        db.subjects.insert_many(subjects)
    if faculty:
        db.faculty.insert_many(faculty)
    if student_groups:
        db.student_groups.insert_many(student_groups)

    db.timing_config.insert_one(_default_timing_config())

    return {
        "classrooms": len(classrooms),
        "subjects": len(subjects),
        "faculty": len(faculty),
        "student_groups": len(student_groups),
    }


def load_assignment_data(db, csv_root, assignments):
    """
    Build timetable input collections from current faculty-assignment output.

    FIX: Previously, subjects with type "lab" were not being classified as
    Practical because the normalisation only checked for "practical".
    Both "practical" and "lab" are now correctly mapped to subject_type
    "Practical" and given requires_lab=True, ensuring the generator will
    seek a lab room for these sessions.
    """
    base = Path(csv_root)
    if not assignments:
        return {
            "classrooms": 0,
            "subjects": 0,
            "faculty": 0,
            "student_groups": 0,
            "assignments": 0,
        }

    classrooms = _read_classrooms_csv(base / "classrooms.csv")
    faculty_limits = _read_faculty_limits(base / "faculty.csv")

    faculty_subjects = defaultdict(set)
    faculty_names = {}
    subject_map = {}
    active_group_divisions = defaultdict(set)

    for item in assignments:
        course_id = str(item["course_id"]).strip()
        semester = int(item["semester"])
        division = str(item["division"]).strip()
        subject_id = str(item["subject_id"]).strip()
        faculty_id = str(item["faculty_id"]).strip()

        active_group_divisions[(course_id, semester)].add(division)
        faculty_subjects[faculty_id].add(subject_id)
        faculty_names[faculty_id] = str(item.get("faculty_name", faculty_id)).strip() or faculty_id

        # FIX: normalise type — "lab" must be treated as practical so the
        # timetable generator classifies the subject correctly and assigns a
        # lab room instead of a theory classroom.
        raw_type = str(item.get("type", "")).strip().lower()
        is_practical = raw_type in ("practical", "lab")

        subject_map[(course_id, semester, subject_id)] = {
            "subject_code": subject_id,
            "subject_name": str(item.get("subject_name", subject_id)).strip(),
            "branch": course_id,
            "semester": semester,
            "subject_type": "Practical" if is_practical else "Theory",
            "credits": int(item.get("credits", 1)),
            "priority": "core",
            "requires_lab": is_practical,
            "lab_batch_size": 30 if is_practical else None,
        }

    subjects = list(subject_map.values())

    faculty = []
    for faculty_id, subjects_set in faculty_subjects.items():
        details = faculty_limits.get(faculty_id, {})
        digits = "".join(filter(str.isdigit, faculty_id))
        faculty_num = int(digits) if digits else 0
        preferred_time = "morning" if faculty_num % 3 == 0 else ("afternoon" if faculty_num % 3 == 1 else "any")
        faculty.append(
            {
                "faculty_id": faculty_id,
                "name": faculty_names.get(faculty_id, details.get("name", faculty_id)),
                "subjects": sorted(subjects_set),
                "max_hours_per_week": details.get("max_hours_per_week", 18),
                "preferred_time": preferred_time,
                "unavailable_days": [],
            }
        )

    division_student_count = {}
    with open(base / "divisions.csv", "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            course_id = str(row["course_id"]).strip()
            semester = int(row["semester"])
            division = str(row["division"]).strip()
            division_student_count[(course_id, semester, division)] = int(row["students"])

    student_groups = []
    for (course_id, semester), divisions in active_group_divisions.items():
        group_id = f"{course_id}_SEM{semester}"
        division_list = []
        for division in sorted(divisions):
            student_count = division_student_count.get((course_id, semester, division), 60)
            division_list.append({"division_name": division, "student_count": student_count})
        if division_list:
            student_groups.append(
                {
                    "group_id": group_id,
                    "branch": course_id,
                    "semester": semester,
                    "divisions": division_list,
                }
            )

    db.classrooms.delete_many({})
    db.subjects.delete_many({})
    db.faculty.delete_many({})
    db.student_groups.delete_many({})
    db.timetables.delete_many({})
    db.faculty_assignments.delete_many({})

    if classrooms:
        db.classrooms.insert_many(classrooms)
    if subjects:
        db.subjects.insert_many(subjects)
    if faculty:
        db.faculty.insert_many(faculty)
    if student_groups:
        db.student_groups.insert_many(student_groups)
    if assignments:
        db.faculty_assignments.insert_many(assignments)

    if not db.timing_config.find_one({"config_id": "default"}):
        db.timing_config.insert_one(_default_timing_config())

    return {
        "classrooms": len(classrooms),
        "subjects": len(subjects),
        "faculty": len(faculty),
        "student_groups": len(student_groups),
        "assignments": len(assignments),
    }