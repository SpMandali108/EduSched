import pandas as pd
import os
from flask import Blueprint, render_template, jsonify, request

MAX_OVERLOAD = 1.25

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

    faculty["theory_count"] = 0
    faculty["practical_count"] = 0

    faculty["preferences"] = faculty["subject_preferences"].fillna("").apply(
        lambda x: set(str(x).split(";"))
    )

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
# TASK BUILDING
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
                "type": sub["type"].lower(),
                "credits": sub["credits"],
                "hours": get_hours(sub)
            })

    return tasks, faculty_list


# =========================
# ASSIGNMENT ENGINE
# =========================
def generate_assignments(sem_type="odd"):
    tasks, faculty_list = build_tasks(sem_type)
    assignments = []

    def max_allowed(fac):
        return fac["max_hours"] * MAX_OVERLOAD

    for task in tasks:
        sub_id = task["subject_id"]
        dept = task["department"]

        valid = []

        for fac in faculty_list:
            if fac["department"] != dept:
                continue

            # 🔥 HARD CAP BLOCK
            if fac["current_hours"] >= max_allowed(fac):
                continue

            if fac["current_hours"] + task["hours"] > max_allowed(fac):
                continue

            valid.append(fac)

        if not valid:
            continue

        avg_load = sum(f["current_hours"] for f in faculty_list) / len(faculty_list)

        scored = []

        for fac in valid:
            score = 0

            # 🔥 PRIMARY: LOAD BALANCE (VERY STRONG)
            score -= fac["current_hours"] * 30

            diff = fac["current_hours"] - avg_load
            score -= diff * 40

            # 🔥 PRIORITIZE LOW LOAD
            if fac["current_hours"] < avg_load:
                score += 80

            # 🔥 TYPE BALANCE (STRONG)
            if task["type"] == "theory":
                if fac["theory_count"] > fac["practical_count"]:
                    score -= 50
                else:
                    score += 20
            else:
                if fac["practical_count"] > fac["theory_count"]:
                    score -= 50
                else:
                    score += 20

            # 🔥 SUBJECT REUSE (WEAK NOW)
            if sub_id in fac["unique_subjects"]:
                score += 10

            # 🔥 PREFERENCES (LOW PRIORITY)
            if sub_id in fac["preferences"]:
                score += 10

            scored.append((fac, score))

        scored.sort(key=lambda x: (-x[1], x[0]["current_hours"]))
        best = scored[0][0]

        # 🔥 FINAL HARD CHECK (CRITICAL FIX)
        if best["current_hours"] + task["hours"] > max_allowed(best):
            continue

        # UPDATE
        best["current_hours"] += task["hours"]
        best["unique_subjects"].add(sub_id)

        if task["type"] == "theory":
            best["theory_count"] += 1
        else:
            best["practical_count"] += 1

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


def get_all_assignments():
    return generate_assignments("odd") + generate_assignments("even")


@facultyPreference.route("/generate-assignment")
def generate_assignment_api():
    try:
        sem_type = request.args.get("sem", "odd")
        return jsonify({"assignments": generate_assignments(sem_type)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "assignments": []}), 500


@facultyPreference.route("/faculty-assignment")
def faculty_page():
    return render_template("facultyPreference.html")