"""
API Routes for all modules
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List
from models import *
from datetime import datetime


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
