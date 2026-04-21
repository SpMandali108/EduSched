import pandas as pd
import os
from flask import Blueprint, render_template, jsonify, request

# =========================
# PATH
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

facultyPreference = Blueprint("facultyPreference", __name__)

# =========================
# LOAD DATA
# =========================
def load_data():
    faculty = pd.read_csv(os.path.join(DATA_DIR, "faculty.csv"))
    faculty.columns = faculty.columns.str.strip().str.lower()

    faculty["department"] = faculty["dept_id"].astype(str).str.upper()
    faculty["max_hours"] = faculty.get("max_hours_per_week", 34)
    faculty["current_hours"] = 0
    faculty["unique_subjects"] = [set() for _ in range(len(faculty))]

    # preferences
    if "subject_preferences" in faculty.columns:
        faculty["preferences"] = faculty["subject_preferences"].fillna("").apply(
            lambda x: set(str(x).split(";"))
        )
    else:
        faculty["preferences"] = [set() for _ in range(len(faculty))]

    subjects = pd.read_csv(os.path.join(DATA_DIR, "subjects.csv"))
    subjects.columns = subjects.columns.str.strip().str.lower()
    subjects["name"] = subjects["subject_name"]
    subjects["department"] = subjects["dept_id"].astype(str).str.upper()

    subject_dict = {
        row["subject_id"]: row.to_dict()
        for _, row in subjects.iterrows()
    }

    course_map = pd.read_csv(os.path.join(DATA_DIR, "course_subject_map.csv"))
    course_map.columns = course_map.columns.str.strip().str.lower()

    divisions = pd.read_csv(os.path.join(DATA_DIR, "divisions.csv"))
    divisions.columns = divisions.columns.str.strip().str.lower()

    return faculty.to_dict("records"), subject_dict, course_map, divisions


# =========================
# HOURS
# =========================
def get_hours(sub):
    return sub["credits"] * 2 if sub["type"] == "practical" else sub["credits"]


# =========================
# BUILD TASKS (SEM FILTERED)
# =========================
def build_tasks(sem_type):
    faculty_list, subject_dict, course_map, divisions = load_data()

    tasks = []

    for _, div in divisions.iterrows():
        for _, row in course_map.iterrows():

            if div["course_id"] != row["course_id"]:
                continue
            if div["semester"] != row["semester"]:
                continue

            sem = int(row["semester"])
            course = str(row["course_id"]).upper()

            # 🔥 SEM FILTER HERE (IMPORTANT FIX)
            if sem_type == "odd":
                if sem not in [1, 3, 5, 7]:
                    continue
            else:
                if sem not in [2, 4, 6]:
                    continue
                if sem == 4 and "PG" in course:
                    continue

            sub = subject_dict.get(row["subject_id"])
            if not sub:
                continue

            tasks.append({
                "course_id": row["course_id"],
                "semester": sem,
                "division": div["division"],
                "subject_id": sub["subject_id"],
                "subject_name": sub["name"],
                "department": sub["department"],
                "type": sub["type"],
                "credits": sub["credits"],
                "hours": get_hours(sub)
            })

    print(f"TOTAL TASKS ({sem_type}):", len(tasks))
    return tasks, faculty_list


# =========================
# ASSIGNMENT ENGINE
# =========================
def generate_assignments(sem_type):
    tasks, faculty_list = build_tasks(sem_type)

    assignments = []
    subject_anchor = {}

    def can_assign(fac, hours):
        return fac["current_hours"] + hours <= fac["max_hours"] + 2

    for task in tasks:
        sub_id = task["subject_id"]
        dept = task["department"]

        valid = []

        # strict filter
        for fac in faculty_list:
            if fac["department"] != dept:
                continue

            if not can_assign(fac, task["hours"]):
                continue

            if sub_id not in fac["unique_subjects"] and len(fac["unique_subjects"]) >= 5:
                continue

            valid.append(fac)

        # relaxed
        if not valid:
            for fac in faculty_list:
                if fac["department"] != dept:
                    continue

                if fac["current_hours"] <= fac["max_hours"] + 2:
                    valid.append(fac)

        if not valid:
            continue

        avg_load = sum(f["current_hours"] for f in faculty_list) / len(faculty_list)

        # scoring
        scored = []
        for fac in valid:
            score = 0

            score -= fac["current_hours"] * 12

            if sub_id in fac["unique_subjects"]:
                score += 60
            else:
                if len(fac["unique_subjects"]) >= 3:
                    score -= 30

            if fac["current_hours"] > avg_load:
                score -= 40

            if sub_id in fac["preferences"]:
                score += 40

            scored.append((fac, score))

        scored.sort(key=lambda x: (-x[1], x[0]["current_hours"]))
        best = scored[0][0]

        # anchor
        if sub_id in subject_anchor:
            anchor = subject_anchor[sub_id]
            if anchor in valid and can_assign(anchor, task["hours"]):
                best = anchor

        # update
        best["current_hours"] += task["hours"]
        best["unique_subjects"].add(sub_id)

        if sub_id not in subject_anchor:
            subject_anchor[sub_id] = best

        assignments.append({
            "course_id": task["course_id"],
            "semester": task["semester"],
            "division": task["division"],
            "subject_id": task["subject_id"],
            "subject_name": task["subject_name"],
            "faculty_id": best["faculty_id"],
            "faculty_name": best["name"],
            "type": task["type"],
            "credits": task["credits"],
            "assigned_hours": best["current_hours"],
            "max_hours": best["max_hours"]
        })

    return assignments


# =========================
# API
# =========================
@facultyPreference.route("/generate-assignment")
def generate_assignment_api():
    try:
        sem_type = request.args.get("sem", "odd")
        assignments = generate_assignments(sem_type)
        return jsonify({"assignments": assignments})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "assignments": []}), 500


# =========================
# PAGE
# =========================
@facultyPreference.route("/faculty-assignment")
def faculty_page():
    return render_template("facultyPreference.html")