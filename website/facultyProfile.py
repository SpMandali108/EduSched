import pandas as pd
import os
from flask import Blueprint, render_template

# =========================
# PATH
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

facultyProfile = Blueprint("facultyProfile", __name__)

# =========================
# LOAD DATA
# =========================
def load_faculty():
    faculty = pd.read_csv(os.path.join(DATA_DIR, "faculty.csv"))
    faculty.columns = faculty.columns.str.strip().str.lower()

    # map fields
    faculty["max_hours"] = faculty.get("max_hours_per_week", 34)

    return faculty


# =========================
# ASSIGNMENTS (reuse engine)
# =========================
def get_all_assignments():
    from .facultyPreference import generate_assignments
    return generate_assignments()


# =========================
# ROUTE
# =========================
@facultyProfile.route("/faculty/<faculty_id>")
def faculty_detail(faculty_id):

    faculty_df = load_faculty()

    # =========================
    # FIND FACULTY
    # =========================
    faculty_row = faculty_df[
        faculty_df["faculty_id"].astype(str) == str(faculty_id)
    ]

    if faculty_row.empty:
        return f"Faculty {faculty_id} not found"

    faculty = faculty_row.iloc[0].to_dict()

    # =========================
    # GET ASSIGNMENTS
    # =========================
    assignments = get_all_assignments()

    faculty_subjects = [
        a for a in assignments
        if str(a["faculty_id"]) == str(faculty_id)
    ]

    # =========================
    # CALCULATE LOAD
    # =========================
    total_load = 0

    for s in faculty_subjects:
        if s["type"].lower() == "practical":
            total_load += s["credits"] * 2
        else:
            total_load += s["credits"]

    # =========================
    # SAFE DEFAULTS (important)
    # =========================
    faculty.setdefault("name", "Faculty")
    faculty.setdefault("dept_id", "NA")
    faculty.setdefault("experience", 0)
    faculty.setdefault("max_hours", 34)

    # =========================
    # RENDER
    # =========================
    return render_template(
        "facultyProfile.html",
        faculty=faculty,
        subjects=faculty_subjects,
        total_load=total_load
    )