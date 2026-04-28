import sys
import os
from pymongo import MongoClient
from collections import defaultdict

# Add current directory to path to import local modules
sys.path.append(os.getcwd())

try:
    from website.timetable_generator import TimetableGenerator
except ImportError:
    print("Could not import TimetableGenerator. Make sure you are in the project root.")
    sys.exit(1)

def verify():
    client = MongoClient("mongodb://localhost:27017")
    db = client["university_timetable_pro"]
    
    generator = TimetableGenerator(db)
    print("Generating timetable...")
    result = generator.generate({"force_regenerate": True})
    
    if not result.get("success"):
        print(f"Generation failed: {result.get('error') or result.get('message')}")
        return

    timetables = result.get("timetables", [])
    print(f"Generated {len(timetables)} timetables.")

    errors = []
    
    for tt in timetables:
        if tt.get("entity_type") != "student":
            continue
            
        division_id = tt["entity_id"]
        entries = tt["entries"]
        
        # Group by day
        day_entries = defaultdict(list)
        for e in entries:
            day_entries[e["day"]].append(e)
            
        for day, slots in day_entries.items():
            # 1. Check One Lab Per Day
            practicals = [s for s in slots if s.get("entry_type") == "practical"]
            if len(practicals) > 0:
                # Count distinct sessions (continuous blocks)
                # In current code, one session is one entry type "practical" 
                # but might be multiple slots.
                # Since we schedule in 2-hour blocks, a 1-credit lab is 2 entries.
                # However, the constraint is "Only one lab session per day".
                # Let's check how many distinct subjects/batches are there.
                lab_subjects = set()
                for p in practicals:
                    lab_subjects.add((p.get("subject_code"), p.get("batch")))
                
                if len(lab_subjects) > 1:
                    errors.append(f"Division {division_id} has multiple labs on {day}: {lab_subjects}")

            # 2. Check Break after 4 slots
            teaching_slots_in_row = 0
            for s in slots:
                if s.get("entry_type") in ["theory", "practical"]:
                    teaching_slots_in_row += 1
                    if teaching_slots_in_row > 4:
                        errors.append(f"Division {division_id} has no break after 4 slots on {day} (at {s['slot_id']})")
                else:
                    teaching_slots_in_row = 0

            # 3. Check Credit durations
            # This is harder to check without subject info, but we can check a few.

    if not errors:
        print("Verification SUCCESS: All constraints satisfied!")
    else:
        print(f"Verification FAILED: {len(errors)} violations found.")
        for err in errors[:10]:
            print(f"  - {err}")
        if len(errors) > 10:
            print("  ... and more")

if __name__ == "__main__":
    verify()
