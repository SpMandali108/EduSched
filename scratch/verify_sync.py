import sys
import os
from pymongo import MongoClient

# Add current directory to path
sys.path.append(os.getcwd())

from website.facultyPreference import generate_assignments

def verify_sync():
    print("Testing ODD semester sync...")
    odd_assignments = generate_assignments("odd")
    odd_sems = set(a["semester"] for a in odd_assignments)
    print(f"Odd Assignments: {len(odd_assignments)}, Semesters: {odd_sems}")
    
    print("\nTesting EVEN semester sync...")
    even_assignments = generate_assignments("even")
    even_sems = set(a["semester"] for a in even_assignments)
    print(f"Even Assignments: {len(even_assignments)}, Semesters: {even_sems}")

    if all(s in [1, 3, 5, 7] for s in odd_sems) and all(s in [2, 4, 6] for s in even_sems):
        print("\nSUCCESS: Logic is correct!")
    else:
        print("\nFAILURE: Logic is leaking semesters!")

if __name__ == "__main__":
    verify_sync()
