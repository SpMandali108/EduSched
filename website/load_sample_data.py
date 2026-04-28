"""
CSV Data Loader for University Timetable System
Reads CSV files and populates MongoDB with real university data
"""

import asyncio
import csv
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "university_timetable_pro"

# CSV file paths (relative to this script)
CSV_FILES = {
    "classrooms": "classrooms.csv",
    "faculty": "faculty.csv",
    "subjects": "subjects.csv",
    "students": "student.csv"
}


def read_classrooms_csv(filepath):
    """Read classrooms from CSV file"""
    classrooms = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            room_id = row['room_id'].strip()
            room_type = row['type'].strip().lower()
            capacity = int(row['capacity'])
            
            # Map CSV type to our system
            # lecture -> Theory, lab -> Practical
            if 'lab' in room_type:
                mapped_type = "Practical"
                is_lab = True
            else:
                mapped_type = "Theory"
                is_lab = False
            
            classroom = {
                "classroom_id": room_id,
                "capacity": capacity,
                "room_type": mapped_type,
                "is_smart_classroom": capacity >= 80,  # Assume large rooms are smart
                "lab_type": "Computer Lab" if is_lab else None
            }
            classrooms.append(classroom)
    
    return classrooms


def read_faculty_csv(filepath):
    """Read faculty from CSV file with robust error handling"""
    faculty_list = []
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f: # -sig handles hidden BOM markers
            reader = csv.DictReader(f)
            
            # Print columns to debug if it fails again
            # print(f"Detected columns: {reader.fieldnames}")

            for row_num, row in enumerate(reader, start=2):
                try:
                    # 1. Basic cleaning and validation
                    f_id_raw = row.get('faculty_id', '').strip()
                    name = row.get('name', 'Unknown').strip()
                    
                    if not f_id_raw or not name:
                        continue # Skip empty rows

                    # 2. Parse subjects safely
                    subjects_str = row.get('subjects', '').strip().strip('"')
                    subjects = [s.strip() for s in subjects_str.split(',') if s.strip()]
                    
                    # 3. Handle max_hours (default to 18 if empty/invalid)
                    raw_hours = row.get('max_hours_per_week', '').strip()
                    max_hours = int(raw_hours) if raw_hours.isdigit() else 18
                    
                    # 4. Handle faculty_num for preferred_time calculation
                    # Removes 'F' and handles cases where ID is just a number
                    id_digits = "".join(filter(str.isdigit, f_id_raw))
                    faculty_num = int(id_digits) if id_digits else 0
                    
                    if faculty_num % 3 == 0:
                        preferred_time = "morning"
                    elif faculty_num % 3 == 1:
                        preferred_time = "afternoon"
                    else:
                        preferred_time = "any"
                    
                    faculty = {
                        "faculty_id": f_id_raw,
                        "name": name,
                        "subjects": subjects,
                        "max_hours_per_week": max_hours,
                        "preferred_time": preferred_time,
                        "unavailable_days": []
                    }
                    faculty_list.append(faculty)

                except Exception as e:
                    print(f"  ⚠️ Row {row_num}: Skipping due to error: {e}")
                    continue
                    
    except Exception as e:
        print(f"  ❌ Critical error reading CSV: {e}")
    
    return faculty_list


def read_subjects_csv(filepath):
    """Read subjects from CSV file"""
    subjects_list = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subject_id = row['subject_id'].strip()
            subject_name = row['subject_name'].strip()
            branch = row['branch'].strip()
            subject_type = row['type'].strip()
            credits = int(row['credits'])
            semester = int(row['sem'])
            
            # Determine if it's practical (ends with P or type is Practical)
            is_practical = subject_id.endswith('P') or 'practical' in subject_type.lower()
            
            # Determine priority (all core for now, can be modified)
            priority = "core"
            
            subject = {
                "subject_code": subject_id,
                "subject_name": subject_name,
                "branch": branch,
                "semester": semester,
                "subject_type": "Practical" if is_practical else "Theory",
                "credits": credits,
                "priority": priority,
                "requires_lab": is_practical,
                "lab_batch_size": 30 if is_practical else None
            }
            subjects_list.append(subject)
    
    return subjects_list


def read_students_csv(filepath):
    """Read student groups from CSV file"""
    # First, group students by branch and semester
    from collections import defaultdict
    
    groups_dict = defaultdict(lambda: {"branch": "", "semester": 0, "divisions": []})
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            branch = row['Branch'].strip()
            semester = int(row['semester'])
            division = row['division'].strip()
            student_count = int(row['students'])
            
            group_key = f"{branch}_SEM{semester}"
            
            if not groups_dict[group_key]["branch"]:
                groups_dict[group_key]["branch"] = branch
                groups_dict[group_key]["semester"] = semester
            
            groups_dict[group_key]["divisions"].append({
                "division_name": division,
                "student_count": student_count
            })
    
    # Convert to list format
    student_groups = []
    for group_id, group_data in groups_dict.items():
        student_group = {
            "group_id": group_id,
            "branch": group_data["branch"],
            "semester": group_data["semester"],
            "divisions": group_data["divisions"]
        }
        student_groups.append(student_group)
    
    return student_groups


async def load_sample_data():
    """Load sample data from CSV files into MongoDB"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    print("=" * 60)
    print("  LOADING UNIVERSITY DATA FROM CSV FILES")
    print("=" * 60)
    
    # Clear existing data
    print("\n🗑️  Clearing existing data...")
    await db.classrooms.delete_many({})
    await db.subjects.delete_many({})
    await db.faculty.delete_many({})
    await db.student_groups.delete_many({})
    await db.timing_config.delete_many({})
    await db.timetables.delete_many({})
    print("  ✅ Cleared all collections")
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Load Classrooms
    print("\n📚 Loading classrooms from CSV...")
    try:
        classrooms_path = script_dir / CSV_FILES["classrooms"]
        classrooms = read_classrooms_csv(classrooms_path)
        if classrooms:
            await db.classrooms.insert_many(classrooms)
            print(f"  ✅ Added {len(classrooms)} classrooms")
            
            # Show breakdown
            theory_count = sum(1 for c in classrooms if c["room_type"] == "Theory")
            lab_count = sum(1 for c in classrooms if c["room_type"] == "Practical")
            print(f"     - Theory rooms: {theory_count}")
            print(f"     - Labs: {lab_count}")
        else:
            print("  ⚠️  No classrooms found")
    except FileNotFoundError:
        print(f"  ❌ File not found: {CSV_FILES['classrooms']}")
        print(f"     Please place CSV files in: {script_dir}")
    except Exception as e:
        print(f"  ❌ Error loading classrooms: {e}")
    
    # Load Faculty
    print("\n👨‍🏫 Loading faculty from CSV...")
    try:
        faculty_path = script_dir / CSV_FILES["faculty"]
        faculty = read_faculty_csv(faculty_path)
        if faculty:
            await db.faculty.insert_many(faculty)
            print(f"  ✅ Added {len(faculty)} faculty members")
            
            # Show sample
            print(f"     Sample: {faculty[0]['name']} teaches {len(faculty[0]['subjects'])} subjects")
        else:
            print("  ⚠️  No faculty found")
    except FileNotFoundError:
        print(f"  ❌ File not found: {CSV_FILES['faculty']}")
    except Exception as e:
        print(f"  ❌ Error loading faculty: {e}")
    
    # Load Subjects
    print("\n📖 Loading subjects from CSV...")
    try:
        subjects_path = script_dir / CSV_FILES["subjects"]
        subjects = read_subjects_csv(subjects_path)
        if subjects:
            await db.subjects.insert_many(subjects)
            print(f"  ✅ Added {len(subjects)} subjects")
            
            # Show breakdown
            theory_count = sum(1 for s in subjects if s["subject_type"] == "Theory")
            practical_count = sum(1 for s in subjects if s["subject_type"] == "Practical")
            print(f"     - Theory subjects: {theory_count}")
            print(f"     - Practical subjects: {practical_count}")
            
            # Show branches
            branches = set(s["branch"] for s in subjects)
            print(f"     - Branches: {', '.join(sorted(branches))}")
        else:
            print("  ⚠️  No subjects found")
    except FileNotFoundError:
        print(f"  ❌ File not found: {CSV_FILES['subjects']}")
    except Exception as e:
        print(f"  ❌ Error loading subjects: {e}")
    
    # Load Students
    print("\n👥 Loading student groups from CSV...")
    try:
        students_path = script_dir / CSV_FILES["students"]
        student_groups = read_students_csv(students_path)
        if student_groups:
            await db.student_groups.insert_many(student_groups)
            print(f"  ✅ Added {len(student_groups)} student groups")
            
            # Show details
            total_divisions = sum(len(g["divisions"]) for g in student_groups)
            total_students = sum(
                sum(d["student_count"] for d in g["divisions"]) 
                for g in student_groups
            )
            print(f"     - Total divisions: {total_divisions}")
            print(f"     - Total students: {total_students}")
            
            # Show breakdown by branch
            branch_counts = {}
            for group in student_groups:
                branch = group["branch"]
                if branch not in branch_counts:
                    branch_counts[branch] = 0
                branch_counts[branch] += sum(d["student_count"] for d in group["divisions"])
            
            for branch, count in sorted(branch_counts.items()):
                print(f"     - {branch}: {count} students")
        else:
            print("  ⚠️  No student groups found")
    except FileNotFoundError:
        print(f"  ❌ File not found: {CSV_FILES['students']}")
    except Exception as e:
        print(f"  ❌ Error loading students: {e}")
    
    # Add default timing configuration
    print("\n⏰ Adding default timing configuration...")
    timing_config = {
        "config_id": "default",
        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "time_slots": [
            {"slot_id": "S1", "start_time": "09:00", "end_time": "10:00", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S2", "start_time": "10:00", "end_time": "11:00", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S3", "start_time": "11:00", "end_time": "11:15", "is_break": True, "slot_type": "break"},
            {"slot_id": "S4", "start_time": "11:15", "end_time": "12:15", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S5", "start_time": "12:15", "end_time": "13:15", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S6", "start_time": "13:15", "end_time": "14:00", "is_break": True, "slot_type": "break"},
            {"slot_id": "S7", "start_time": "14:00", "end_time": "15:00", "is_break": False, "slot_type": "theory"},
            {"slot_id": "S8", "start_time": "15:00", "end_time": "16:00", "is_break": False, "slot_type": "theory"},
        ],
        "theory_duration_minutes": 60,
        "practical_duration_slots": 2
    }
    await db.timing_config.insert_one(timing_config)
    print("  ✅ Added timing configuration")
    print(f"     - Working days: {', '.join(timing_config['working_days'])}")
    print(f"     - Slots per day: {len([s for s in timing_config['time_slots'] if not s['is_break']])} (+ 2 breaks)")
    print(f"     - Hours: 9:00 AM - 4:00 PM")
    
    # Summary
    print("\n" + "=" * 60)
    print("  ✨ DATA LOADING COMPLETE!")
    print("=" * 60)
    
    # Get final counts
    classroom_count = await db.classrooms.count_documents({})
    subject_count = await db.subjects.count_documents({})
    faculty_count = await db.faculty.count_documents({})
    student_group_count = await db.student_groups.count_documents({})
    
    print("\n📊 FINAL DATABASE SUMMARY:")
    print(f"  ✓ Classrooms: {classroom_count}")
    print(f"  ✓ Subjects: {subject_count}")
    print(f"  ✓ Faculty: {faculty_count}")
    print(f"  ✓ Student Groups: {student_group_count}")
    print(f"  ✓ Timing Config: Configured")
    
    print("\n🎯 NEXT STEPS:")
    print("  1. Start the backend: python main.py")
    print("  2. Start the frontend: python -m http.server 8080")
    print("  3. Open browser: http://localhost:8080")
    print("  4. Configure timing if needed: Data Entry → Timing")
    print("  5. Generate timetable: Dashboard → Generate Timetable")
    
    print("\n✨ Ready to generate timetables!")
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(load_sample_data())