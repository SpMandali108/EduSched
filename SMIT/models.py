"""
Pydantic models for data validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import time

# Classroom Models
class Classroom(BaseModel):
    classroom_id: str = Field(..., description="Unique classroom identifier")
    capacity: int = Field(..., ge=1, description="Seating capacity")
    room_type: str = Field(..., description="Theory or Practical")
    is_smart_classroom: bool = Field(default=False)
    lab_type: Optional[str] = Field(None, description="Type of lab if practical")

class ClassroomUpdate(BaseModel):
    capacity: Optional[int] = Field(None, ge=1)
    room_type: Optional[str] = None
    is_smart_classroom: Optional[bool] = None
    lab_type: Optional[str] = None

# Subject Models
class Subject(BaseModel):
    subject_code: str = Field(..., description="Unique subject code")
    subject_name: str = Field(..., description="Subject name")
    branch: str = Field(..., description="Branch/Department")
    semester: int = Field(..., ge=1, le=8)
    subject_type: str = Field(..., description="Theory or Practical")
    credits: int = Field(..., ge=1, description="Number of lectures per week")
    priority: str = Field(default="core", description="core or elective")
    requires_lab: bool = Field(default=False)
    lab_batch_size: Optional[int] = Field(None, description="Students per batch for practicals")

class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = None
    branch: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=8)
    subject_type: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1)
    priority: Optional[str] = None
    requires_lab: Optional[bool] = None
    lab_batch_size: Optional[int] = None

# Faculty Models
class Faculty(BaseModel):
    faculty_id: str = Field(..., description="Unique faculty identifier")
    name: str = Field(..., description="Faculty name")
    subjects: List[str] = Field(..., description="List of subject codes")
    max_hours_per_week: int = Field(..., ge=1, description="Maximum teaching hours")
    preferred_time: str = Field(default="any", description="morning, afternoon, or any")
    unavailable_days: List[str] = Field(default=[], description="List of unavailable days")

class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    subjects: Optional[List[str]] = None
    max_hours_per_week: Optional[int] = Field(None, ge=1)
    preferred_time: Optional[str] = None
    unavailable_days: Optional[List[str]] = None

# Student Models
class Division(BaseModel):
    division_name: str = Field(..., description="Division identifier (A, B, C)")
    student_count: int = Field(..., ge=1, description="Number of students")

class StudentGroup(BaseModel):
    branch: str = Field(..., description="Branch/Department")
    semester: int = Field(..., ge=1, le=8)
    divisions: List[Division] = Field(..., description="List of divisions")

class StudentGroupUpdate(BaseModel):
    branch: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=8)
    divisions: Optional[List[Division]] = None

# Timing Models
class TimeSlot(BaseModel):
    slot_id: str = Field(..., description="Slot identifier")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")
    is_break: bool = Field(default=False)
    slot_type: str = Field(default="theory", description="theory, practical, or break")

class TimingConfiguration(BaseModel):
    working_days: List[str] = Field(..., description="List of working days")
    time_slots: List[TimeSlot] = Field(..., description="Daily time slots")
    theory_duration_minutes: int = Field(default=60)
    practical_duration_slots: int = Field(default=2, description="Continuous slots for practicals")

class TimingUpdate(BaseModel):
    working_days: Optional[List[str]] = None
    time_slots: Optional[List[TimeSlot]] = None
    theory_duration_minutes: Optional[int] = None
    practical_duration_slots: Optional[int] = None

# Timetable Models
class TimetableEntry(BaseModel):
    day: str
    slot_id: str
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    faculty_id: Optional[str] = None
    faculty_name: Optional[str] = None
    classroom_id: Optional[str] = None
    entry_type: str = Field(default="theory", description="theory, practical, or break")
    batch: Optional[str] = Field(None, description="Batch identifier for practicals")

class Timetable(BaseModel):
    timetable_id: str
    entity_type: str = Field(..., description="student, faculty, or classroom")
    entity_id: str = Field(..., description="ID of student group, faculty, or classroom")
    entries: List[TimetableEntry]
    generated_at: str
    version: int = Field(default=1)

class TimetableGeneration(BaseModel):
    branches: Optional[List[str]] = Field(None, description="Generate for specific branches")
    semesters: Optional[List[int]] = Field(None, description="Generate for specific semesters")
    force_regenerate: bool = Field(default=False)

class TimetableEdit(BaseModel):
    timetable_id: str
    day: str
    slot_id: str
    subject_code: Optional[str] = None
    faculty_id: Optional[str] = None
    classroom_id: Optional[str] = None
    entry_type: Optional[str] = None
