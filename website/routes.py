"""
API Routes for all modules
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
from models import *
from datetime import datetime
import zipfile
import io
import csv
from pathlib import Path


async def _auto_regenerate_timetables(request: Request):
    """
    Best-effort timetable regeneration after data changes.
    CRUD should still succeed even when generation cannot run yet
    because required master data is incomplete.
    """
    from timetable_generator import TimetableGenerator

    generator = TimetableGenerator(request.app.state.db)
    result = await generator.generate(TimetableGeneration(force_regenerate=True))

    if not result.get("success"):
        print(f"Auto-regenerate skipped: {result.get('error') or result.get('message')}")

# Classroom Routes
classroom_router = APIRouter()

@classroom_router.post("/", status_code=201)
async def create_classroom(classroom: Classroom, request: Request):
    """Create a new classroom"""
    db = request.app.state.db
    
    # Check if classroom already exists
    existing = await db.classrooms.find_one({"classroom_id": classroom.classroom_id})
    if existing:
        raise HTTPException(status_code=400, detail="Classroom already exists")
    
    classroom_dict = classroom.dict()
    classroom_dict["created_at"] = datetime.utcnow().isoformat()
    
    await db.classrooms.insert_one(classroom_dict)
    await _auto_regenerate_timetables(request)
    return {"message": "Classroom created successfully", "classroom_id": classroom.classroom_id}

@classroom_router.get("/")
async def get_all_classrooms(request: Request):
    """Get all classrooms"""
    db = request.app.state.db
    classrooms = await db.classrooms.find({}, {"_id": 0}).to_list(1000)
    return {"classrooms": classrooms, "count": len(classrooms)}

@classroom_router.get("/{classroom_id}")
async def get_classroom(classroom_id: str, request: Request):
    """Get specific classroom"""
    db = request.app.state.db
    classroom = await db.classrooms.find_one({"classroom_id": classroom_id}, {"_id": 0})
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom

@classroom_router.put("/{classroom_id}")
async def update_classroom(classroom_id: str, classroom_update: ClassroomUpdate, request: Request):
    """Update classroom"""
    db = request.app.state.db
    update_data = {k: v for k, v in classroom_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = await db.classrooms.update_one(
        {"classroom_id": classroom_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Classroom updated successfully"}

@classroom_router.delete("/{classroom_id}")
async def delete_classroom(classroom_id: str, request: Request):
    """Delete classroom"""
    db = request.app.state.db
    result = await db.classrooms.delete_one({"classroom_id": classroom_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Classroom deleted successfully"}


# Subject Routes
subject_router = APIRouter()

@subject_router.post("/", status_code=201)
async def create_subject(subject: Subject, request: Request):
    """Create a new subject"""
    db = request.app.state.db
    
    existing = await db.subjects.find_one({"subject_code": subject.subject_code})
    if existing:
        raise HTTPException(status_code=400, detail="Subject already exists")
    
    subject_dict = subject.dict()
    subject_dict["created_at"] = datetime.utcnow().isoformat()
    
    await db.subjects.insert_one(subject_dict)
    await _auto_regenerate_timetables(request)
    return {"message": "Subject created successfully", "subject_code": subject.subject_code}

@subject_router.get("/")
async def get_all_subjects(request: Request, branch: str = None, semester: int = None):
    """Get all subjects with optional filters"""
    db = request.app.state.db
    query = {}
    if branch:
        query["branch"] = branch
    if semester:
        query["semester"] = semester
    
    subjects = await db.subjects.find(query, {"_id": 0}).to_list(1000)
    return {"subjects": subjects, "count": len(subjects)}

@subject_router.get("/{subject_code}")
async def get_subject(subject_code: str, request: Request):
    """Get specific subject"""
    db = request.app.state.db
    subject = await db.subjects.find_one({"subject_code": subject_code}, {"_id": 0})
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@subject_router.put("/{subject_code}")
async def update_subject(subject_code: str, subject_update: SubjectUpdate, request: Request):
    """Update subject"""
    db = request.app.state.db
    update_data = {k: v for k, v in subject_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = await db.subjects.update_one(
        {"subject_code": subject_code},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Subject updated successfully"}

@subject_router.delete("/{subject_code}")
async def delete_subject(subject_code: str, request: Request):
    """Delete subject"""
    db = request.app.state.db
    result = await db.subjects.delete_one({"subject_code": subject_code})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Subject deleted successfully"}


# Faculty Routes
faculty_router = APIRouter()

@faculty_router.post("/", status_code=201)
async def create_faculty(faculty: Faculty, request: Request):
    """Create a new faculty member"""
    db = request.app.state.db
    
    existing = await db.faculty.find_one({"faculty_id": faculty.faculty_id})
    if existing:
        raise HTTPException(status_code=400, detail="Faculty already exists")
    
    faculty_dict = faculty.dict()
    faculty_dict["created_at"] = datetime.utcnow().isoformat()
    
    await db.faculty.insert_one(faculty_dict)
    await _auto_regenerate_timetables(request)
    return {"message": "Faculty created successfully", "faculty_id": faculty.faculty_id}

@faculty_router.get("/")
async def get_all_faculty(request: Request):
    """Get all faculty members"""
    db = request.app.state.db
    faculty = await db.faculty.find({}, {"_id": 0}).to_list(1000)
    return {"faculty": faculty, "count": len(faculty)}

@faculty_router.get("/{faculty_id}")
async def get_faculty(faculty_id: str, request: Request):
    """Get specific faculty member"""
    db = request.app.state.db
    faculty = await db.faculty.find_one({"faculty_id": faculty_id}, {"_id": 0})
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@faculty_router.put("/{faculty_id}")
async def update_faculty(faculty_id: str, faculty_update: FacultyUpdate, request: Request):
    """Update faculty member"""
    db = request.app.state.db
    update_data = {k: v for k, v in faculty_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = await db.faculty.update_one(
        {"faculty_id": faculty_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Faculty updated successfully"}

@faculty_router.delete("/{faculty_id}")
async def delete_faculty(faculty_id: str, request: Request):
    """Delete faculty member"""
    db = request.app.state.db
    result = await db.faculty.delete_one({"faculty_id": faculty_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Faculty deleted successfully"}


# Student Routes
student_router = APIRouter()

@student_router.post("/", status_code=201)
async def create_student_group(student_group: StudentGroup, request: Request):
    """Create a new student group"""
    db = request.app.state.db
    
    # Create unique ID
    group_id = f"{student_group.branch}_SEM{student_group.semester}"
    
    existing = await db.student_groups.find_one({"group_id": group_id})
    if existing:
        raise HTTPException(status_code=400, detail="Student group already exists")
    
    group_dict = student_group.dict()
    group_dict["group_id"] = group_id
    group_dict["created_at"] = datetime.utcnow().isoformat()
    
    await db.student_groups.insert_one(group_dict)
    await _auto_regenerate_timetables(request)
    return {"message": "Student group created successfully", "group_id": group_id}

@student_router.get("/")
async def get_all_student_groups(request: Request):
    """Get all student groups"""
    db = request.app.state.db
    groups = await db.student_groups.find({}, {"_id": 0}).to_list(1000)
    return {"student_groups": groups, "count": len(groups)}

@student_router.get("/{group_id}")
async def get_student_group(group_id: str, request: Request):
    """Get specific student group"""
    db = request.app.state.db
    group = await db.student_groups.find_one({"group_id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Student group not found")
    return group

@student_router.put("/{group_id}")
async def update_student_group(group_id: str, group_update: StudentGroupUpdate, request: Request):
    """Update student group"""
    db = request.app.state.db
    update_data = {k: v for k, v in group_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = await db.student_groups.update_one(
        {"group_id": group_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student group not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Student group updated successfully"}

@student_router.delete("/{group_id}")
async def delete_student_group(group_id: str, request: Request):
    """Delete student group"""
    db = request.app.state.db
    result = await db.student_groups.delete_one({"group_id": group_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student group not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Student group deleted successfully"}


# Timing Routes
timing_router = APIRouter()

@timing_router.post("/", status_code=201)
async def create_timing_config(timing: TimingConfiguration, request: Request):
    """Create or update timing configuration"""
    db = request.app.state.db
    
    timing_dict = timing.dict()
    timing_dict["config_id"] = "default"
    timing_dict["updated_at"] = datetime.utcnow().isoformat()
    
    await db.timing_config.update_one(
        {"config_id": "default"},
        {"$set": timing_dict},
        upsert=True
    )
    
    await _auto_regenerate_timetables(request)
    return {"message": "Timing configuration saved successfully"}

@timing_router.get("/")
async def get_timing_config(request: Request):
    """Get timing configuration"""
    db = request.app.state.db
    config = await db.timing_config.find_one({"config_id": "default"}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Timing configuration not found")
    return config

@timing_router.put("/")
async def update_timing_config(timing_update: TimingUpdate, request: Request):
    """Update timing configuration"""
    db = request.app.state.db
    update_data = {k: v for k, v in timing_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    result = await db.timing_config.update_one(
        {"config_id": "default"},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Timing configuration not found")
    
    await _auto_regenerate_timetables(request)
    return {"message": "Timing configuration updated successfully"}


# Timetable Routes (placeholder - will be implemented in timetable_generator.py)
timetable_router = APIRouter()

@timetable_router.post("/generate")
async def generate_timetable(generation_params: TimetableGeneration, request: Request):
    """Generate timetable"""
    from timetable_generator import TimetableGenerator
    
    db = request.app.state.db
    generator = TimetableGenerator(db)
    
    try:
        result = await generator.generate(generation_params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timetable generation failed: {str(e)}")

@timetable_router.get("/")
async def get_all_timetables(request: Request, entity_type: str = None):
    """Get all timetables"""
    db = request.app.state.db
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    
    timetables = await db.timetables.find(query, {"_id": 0}).to_list(1000)
    return {"timetables": timetables, "count": len(timetables)}

@timetable_router.get("/{timetable_id}")
async def get_timetable(timetable_id: str, request: Request):
    """Get specific timetable"""
    db = request.app.state.db
    timetable = await db.timetables.find_one({"timetable_id": timetable_id}, {"_id": 0})
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    return timetable

@timetable_router.put("/{timetable_id}/edit")
async def edit_timetable(timetable_id: str, edit: TimetableEdit, request: Request):
    """Edit a specific timetable entry"""
    db = request.app.state.db
    
    # Find the timetable
    timetable = await db.timetables.find_one({"timetable_id": timetable_id})
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    # Update the specific entry
    update_data = {k: v for k, v in edit.dict(exclude={"timetable_id", "day", "slot_id"}).items() if v is not None}
    
    result = await db.timetables.update_one(
        {
            "timetable_id": timetable_id,
            "entries.day": edit.day,
            "entries.slot_id": edit.slot_id
        },
        {"$set": {f"entries.$.{k}": v for k, v in update_data.items()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    
    return {"message": "Timetable entry updated successfully"}

@timetable_router.delete("/{timetable_id}")
async def delete_timetable(timetable_id: str, request: Request):
    """Delete timetable"""
    db = request.app.state.db
    result = await db.timetables.delete_one({"timetable_id": timetable_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    return {"message": "Timetable deleted successfully"}

@timetable_router.delete("/")
async def delete_all_timetables(request: Request):
    """Delete all timetables (reset)"""
    db = request.app.state.db
    result = await db.timetables.delete_many({})
    return {"message": f"Deleted {result.deleted_count} timetables"}


# ============================================================================
# Load Data Router - Sample downloads, template downloads, CSV upload
# ============================================================================

load_data_router = APIRouter()

EXPECTED_HEADERS = {
    "classrooms": ["room_id", "type", "capacity"],
    "faculty": ["faculty_id", "name", "subjects", "max_hours_per_week"],
    "students": ["Branch", "semester", "division", "students"],
    "subjects": ["subject_id", "subject_name", "branch", "type", "credits", "sem"]
}

CSV_FILE_MAP = {
    "classrooms": "classrooms.csv",
    "faculty": "faculty.csv",
    "students": "student.csv",
    "subjects": "subjects.csv"
}


def _create_zip_buffer(files_dict: dict) -> io.BytesIO:
    """Create a ZIP buffer from a dict of {filename: file_content_bytes}"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files_dict.items():
            zf.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer


@load_data_router.get("/sample")
async def download_sample_data():
    """Download a ZIP containing all 4 sample CSV files"""
    script_dir = Path(__file__).parent
    files_dict = {}
    for key, filename in CSV_FILE_MAP.items():
        filepath = script_dir / filename
        if filepath.exists():
            files_dict[filename] = filepath.read_bytes()
        else:
            raise HTTPException(status_code=500, detail=f"Sample file not found: {filename}")
    
    zip_buffer = _create_zip_buffer(files_dict)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=sample_data.zip"}
    )


@load_data_router.get("/template")
async def download_template_csv():
    """Download a ZIP containing all 4 CSV templates (headers only)"""
    files_dict = {}
    for key, headers in EXPECTED_HEADERS.items():
        filename = CSV_FILE_MAP[key]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        files_dict[filename] = output.getvalue().encode("utf-8")
    
    zip_buffer = _create_zip_buffer(files_dict)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=template_csv.zip"}
    )


def _read_csv_rows(content: str):
    """Read CSV content and return headers + rows"""
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []
    rows = list(reader)
    return headers, rows


def _parse_classrooms(rows: list) -> list:
    classrooms = []
    for row in rows:
        room_id = row["room_id"].strip()
        room_type = row["type"].strip().lower()
        capacity = int(row["capacity"])
        is_lab = "lab" in room_type
        classrooms.append({
            "classroom_id": room_id,
            "capacity": capacity,
            "room_type": "Practical" if is_lab else "Theory",
            "is_smart_classroom": capacity >= 80,
            "lab_type": "Computer Lab" if is_lab else None
        })
    return classrooms


def _parse_faculty(rows: list) -> list:
    faculty_list = []
    for row in rows:
        f_id = row["faculty_id"].strip()
        name = row["name"].strip()
        subjects_str = row["subjects"].strip().strip('"')
        subjects = [s.strip() for s in subjects_str.split(",") if s.strip()]
        raw_hours = row["max_hours_per_week"].strip()
        max_hours = int(raw_hours) if raw_hours.isdigit() else 18
        id_digits = "".join(filter(str.isdigit, f_id))
        faculty_num = int(id_digits) if id_digits else 0
        if faculty_num % 3 == 0:
            preferred_time = "morning"
        elif faculty_num % 3 == 1:
            preferred_time = "afternoon"
        else:
            preferred_time = "any"
        faculty_list.append({
            "faculty_id": f_id,
            "name": name,
            "subjects": subjects,
            "max_hours_per_week": max_hours,
            "preferred_time": preferred_time,
            "unavailable_days": []
        })
    return faculty_list


def _parse_subjects(rows: list) -> list:
    subjects_list = []
    for row in rows:
        subject_id = row["subject_id"].strip()
        subject_name = row["subject_name"].strip()
        branch = row["branch"].strip()
        subject_type = row["type"].strip()
        credits = int(row["credits"])
        semester = int(row["sem"])
        is_practical = subject_id.endswith("P") or "practical" in subject_type.lower()
        subjects_list.append({
            "subject_code": subject_id,
            "subject_name": subject_name,
            "branch": branch,
            "semester": semester,
            "subject_type": "Practical" if is_practical else "Theory",
            "credits": credits,
            "priority": "core",
            "requires_lab": is_practical,
            "lab_batch_size": 30 if is_practical else None
        })
    return subjects_list


def _parse_students(rows: list) -> list:
    from collections import defaultdict
    groups_dict = defaultdict(lambda: {"branch": "", "semester": 0, "divisions": []})
    for row in rows:
        branch = row["Branch"].strip()
        semester = int(row["semester"])
        division = row["division"].strip()
        student_count = int(row["students"])
        group_key = f"{branch}_SEM{semester}"
        if not groups_dict[group_key]["branch"]:
            groups_dict[group_key]["branch"] = branch
            groups_dict[group_key]["semester"] = semester
        groups_dict[group_key]["divisions"].append({
            "division_name": division,
            "student_count": student_count
        })
    student_groups = []
    for group_id, group_data in groups_dict.items():
        student_groups.append({
            "group_id": group_id,
            "branch": group_data["branch"],
            "semester": group_data["semester"],
            "divisions": group_data["divisions"]
        })
    return student_groups


@load_data_router.post("/upload")
async def upload_csv_files(
    request: Request,
    classrooms: UploadFile = File(...),
    faculty: UploadFile = File(...),
    students: UploadFile = File(...),
    subjects: UploadFile = File(...)
):
    """Upload 4 CSV files, validate, and replace database contents"""
    db = request.app.state.db
    
    # Validate file names
    expected_files = {
        "classrooms": "classrooms.csv",
        "faculty": "faculty.csv",
        "students": "student.csv",
        "subjects": "subjects.csv"
    }
    uploaded = {
        "classrooms": classrooms,
        "faculty": faculty,
        "students": students,
        "subjects": subjects
    }
    for key, upload in uploaded.items():
        if upload.filename != expected_files[key]:
            raise HTTPException(
                status_code=400,
                detail=f"Expected file name '{expected_files[key]}' for {key}, got '{upload.filename}'"
            )
    
    # Read and validate headers
    parsed_data = {}
    for key, upload in uploaded.items():
        content = (await upload.read()).decode("utf-8")
        headers, rows = _read_csv_rows(content)
        expected = EXPECTED_HEADERS[key]
        if headers != expected:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid headers for {upload.filename}. Expected {expected}, got {headers}"
            )
        parsed_data[key] = rows
    
    # Validate subjects: sem must be all odd OR all even
    subject_rows = parsed_data["subjects"]
    sems = set()
    for row in subject_rows:
        sems.add(int(row["sem"]))
    has_odd = any(s % 2 == 1 for s in sems)
    has_even = any(s % 2 == 0 for s in sems)
    if has_odd and has_even:
        raise HTTPException(
            status_code=400,
            detail="Subjects CSV contains both odd and even semesters. Please upload only odd OR only even semesters."
        )
    
    # Parse into database format
    classrooms_data = _parse_classrooms(parsed_data["classrooms"])
    faculty_data = _parse_faculty(parsed_data["faculty"])
    subjects_data = _parse_subjects(parsed_data["subjects"])
    students_data = _parse_students(parsed_data["students"])
    
    # Clear existing collections
    await db.classrooms.delete_many({})
    await db.subjects.delete_many({})
    await db.faculty.delete_many({})
    await db.student_groups.delete_many({})
    await db.timetables.delete_many({})
    
    # Insert new data
    if classrooms_data:
        await db.classrooms.insert_many(classrooms_data)
    if subjects_data:
        await db.subjects.insert_many(subjects_data)
    if faculty_data:
        await db.faculty.insert_many(faculty_data)
    if students_data:
        await db.student_groups.insert_many(students_data)
    
    # Ensure timing config exists (keep existing or add default)
    existing_timing = await db.timing_config.find_one({"config_id": "default"})
    if not existing_timing:
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
    
    # Auto-regenerate timetables
    await _auto_regenerate_timetables(request)
    
    return {
        "message": "Data uploaded successfully",
        "counts": {
            "classrooms": len(classrooms_data),
            "subjects": len(subjects_data),
            "faculty": len(faculty_data),
            "student_groups": len(students_data)
        }
    }


@load_data_router.post("/sample")
async def load_sample_data_from_csv(request: Request):
    """Load sample data from existing CSV files into MongoDB (same as load_sample_data.py)"""
    db = request.app.state.db
    script_dir = Path(__file__).parent

    # Clear existing data
    await db.classrooms.delete_many({})
    await db.subjects.delete_many({})
    await db.faculty.delete_many({})
    await db.student_groups.delete_many({})
    await db.timetables.delete_many({})

    counts = {"classrooms": 0, "subjects": 0, "faculty": 0, "student_groups": 0}

    # Load Classrooms
    try:
        classrooms_path = script_dir / CSV_FILE_MAP["classrooms"]
        if classrooms_path.exists():
            import asyncio
            from load_sample_data import read_classrooms_csv
            classrooms = read_classrooms_csv(classrooms_path)
            if classrooms:
                await db.classrooms.insert_many(classrooms)
                counts["classrooms"] = len(classrooms)
    except Exception as e:
        print(f"Error loading classrooms: {e}")

    # Load Faculty
    try:
        faculty_path = script_dir / CSV_FILE_MAP["faculty"]
        if faculty_path.exists():
            from load_sample_data import read_faculty_csv
            faculty = read_faculty_csv(faculty_path)
            if faculty:
                await db.faculty.insert_many(faculty)
                counts["faculty"] = len(faculty)
    except Exception as e:
        print(f"Error loading faculty: {e}")

    # Load Subjects
    try:
        subjects_path = script_dir / CSV_FILE_MAP["subjects"]
        if subjects_path.exists():
            from load_sample_data import read_subjects_csv
            subjects = read_subjects_csv(subjects_path)
            if subjects:
                await db.subjects.insert_many(subjects)
                counts["subjects"] = len(subjects)
    except Exception as e:
        print(f"Error loading subjects: {e}")

    # Load Students
    try:
        students_path = script_dir / CSV_FILE_MAP["students"]
        if students_path.exists():
            from load_sample_data import read_students_csv
            students = read_students_csv(students_path)
            if students:
                await db.student_groups.insert_many(students)
                counts["student_groups"] = len(students)
    except Exception as e:
        print(f"Error loading students: {e}")

    # Ensure timing config exists
    existing_timing = await db.timing_config.find_one({"config_id": "default"})
    if not existing_timing:
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

    # Auto-regenerate timetables
    await _auto_regenerate_timetables(request)

    return {
        "message": "Sample data loaded successfully",
        "counts": counts
    }


@load_data_router.post("/reset")
async def reset_all_data(request: Request):
    """Delete all stored data from every collection"""
    db = request.app.state.db

    counts = {}
    counts["classrooms"] = (await db.classrooms.delete_many({})).deleted_count
    counts["subjects"] = (await db.subjects.delete_many({})).deleted_count
    counts["faculty"] = (await db.faculty.delete_many({})).deleted_count
    counts["student_groups"] = (await db.student_groups.delete_many({})).deleted_count
    counts["timetables"] = (await db.timetables.delete_many({})).deleted_count
    counts["timing_configs"] = (await db.timing_config.delete_many({})).deleted_count

    return {
        "message": "All data has been reset",
        "deleted_counts": counts
    }
