import sys
import os
from pymongo import MongoClient
from pathlib import Path

# Add current directory to path
sys.path.append(os.getcwd())

from website.facultyPreference import generate_assignments
from website.load_sample_data import load_assignment_data
from website.timetable_generator import TimetableGenerator

def verify_parallel_labs():
    client = MongoClient("mongodb://localhost:27017")
    db = client["university_timetable_pro"]
    
    print("Step 1: Syncing Faculty Assignments (Odd Semester)...")
    # This calls my updated facultyPreference.py which creates multiple tasks per lab
    assignments = generate_assignments("odd")
    
    print("Step 2: Loading assignment data into DB...")
    # This clears the DB and inserts subjects, student_groups, etc.
    load_assignment_data(db, Path("data"), assignments)
    
    print("Step 3: Generating Timetable...")
    generator = TimetableGenerator(db)
    result = generator.generate({"force_regenerate": True})
    
    if not result.get("success"):
        print(f"Generation failed: {result.get('error') or result.get('message')}")
        return

    # Check a specific division that should have multiple batches
    # CSE_UG_SEM1_A (usually 60+ students)
    tt = db.timetables.find_one({"entity_id": "CSE_UG_SEM1_A"})
    if not tt:
        # Try SEM3 if SEM1 was filtered
        tt = db.timetables.find_one({"entity_id": "CSE_UG_SEM3_A"})
        
    if not tt:
        print("Could not find suitable timetable for verification")
        return
        
    print(f"Verifying timetable for {tt['entity_id']}...")
    entries = tt["entries"]
    
    # Group practical entries by subject and day/time
    lab_groups = {} # (subject_code, day, slot_id) -> list of batches
    for e in entries:
        if e.get("entry_type") == "practical":
            key = (e["subject_code"], e["day"], e["slot_id"])
            if key not in lab_groups:
                lab_groups[key] = []
            lab_groups[key].append(e["batch"])
            
    # Check if we have any group with multiple batches
    parallel_found = False
    for key, batches in lab_groups.items():
        if len(batches) > 1:
            print(f"SUCCESS: Found parallel batches for {key[0]} on {key[1]} at {key[2]}: {batches}")
            parallel_found = True
            break
            
    if not parallel_found:
        print("FAILURE: No parallel batches found. Labs might still be scheduled on different days or times.")

if __name__ == "__main__":
    verify_parallel_labs()
