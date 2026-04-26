import sys
import os
from pymongo import MongoClient

# Add current directory to path
sys.path.append(os.getcwd())

from website.timetable_generator import TimetableGenerator

def verify_lab_logic():
    client = MongoClient("mongodb://localhost:27017")
    db = client["university_timetable_pro"]
    
    # Manually insert a 2-credit lab to test scaling
    db.subjects.delete_many({"subject_code": "TEST_LAB_2C"})
    db.subjects.insert_one({
        "subject_code": "TEST_LAB_2C",
        "subject_name": "Test 2-Credit Lab",
        "branch": "CSE_UG",
        "semester": 2,
        "subject_type": "Practical",
        "credits": 2,
        "requires_lab": True,
        "lab_batch_size": 100, # All students in one batch for simplicity
        "schedule_key": "TEST_LAB_2C_practical"
    })
    
    # Ensure there's a faculty and classroom
    if not db.faculty.find_one({"subjects": "TEST_LAB_2C"}):
        fac = db.faculty.find_one()
        if fac:
            db.faculty.update_one({"_id": fac["_id"]}, {"$push": {"subjects": "TEST_LAB_2C"}})
            
    generator = TimetableGenerator(db)
    print("Generating timetable...")
    result = generator.generate({"force_regenerate": True})
    
    if not result.get("success"):
        print(f"Generation failed: {result.get('error') or result.get('message')}")
        return

    # Find the timetable for a SEM 1 division
    # Assuming CSE_UG_SEM1_A exists
    tt = db.timetables.find_one({"entity_id": "CSE_UG_SEM2_A"})
    if not tt:
        print("Could not find timetable for CSE_UG_SEM2_A")
        return
        
    entries = tt["entries"]
    lab_entries = [e for e in entries if e.get("subject_code") == "TEST_LAB_2C"]
    
    print(f"Found {len(lab_entries)} entries for TEST_LAB_2C")
    
    # Group by day
    days = set(e["day"] for e in lab_entries)
    print(f"Scheduled on days: {days}")
    
    if len(days) == 1 and len(lab_entries) == 4:
        print("SUCCESS: 2-credit lab scheduled as one 4-hour block on one day!")
    elif len(days) > 1:
        print(f"FAILURE: Lab scheduled on multiple days: {days}")
    else:
        print(f"FAILURE: Unexpected number of slots ({len(lab_entries)}) or days.")

if __name__ == "__main__":
    verify_lab_logic()
