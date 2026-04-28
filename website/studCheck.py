from flask import Flask, jsonify, render_template, Blueprint
import pandas as pd

studCheck = Blueprint("studCheck", __name__)

# -----------------------
# LOAD DATA (SAFE)
# -----------------------
try:
    departments = pd.read_csv("data/departments.csv")
    courses = pd.read_csv("data/courses.csv")
    divisions = pd.read_csv("data/divisions.csv")
except Exception as e:
    print("Error loading CSV files:", e)
    departments = pd.DataFrame()
    courses = pd.DataFrame()
    divisions = pd.DataFrame()

# -----------------------
# ROUTES
# -----------------------

@studCheck.route("/")
def index():
    return render_template("index.html")


# -----------------------
# GET DEPARTMENTS
# -----------------------
@studCheck.route("/departments")
def get_departments():
    if departments.empty:
        return jsonify({"error": "Departments data not available"}), 500
    
    return jsonify(departments.to_dict(orient="records"))


# -----------------------
# GET COURSES BY DEPARTMENT
# -----------------------
@studCheck.route("/courses/<dept_id>")
def get_courses(dept_id):
    if courses.empty:
        return jsonify({"error": "Courses data not available"}), 500

    data = courses[courses["dept_id"].astype(str) == str(dept_id)]

    return jsonify(data.to_dict(orient="records"))


# -----------------------
# GET SEMESTERS BY COURSE
# -----------------------
@studCheck.route("/semesters/<course_id>")
def get_semesters(course_id):
    if courses.empty:
        return jsonify({"error": "Courses data not available"}), 500

    course_row = courses[courses["course_id"].astype(str) == str(course_id)]

    if course_row.empty:
        return jsonify({"error": "Invalid course_id"}), 404

    max_sem = int(course_row.iloc[0]["semesters"])

    return jsonify(list(range(1, max_sem + 1)))


# -----------------------
# GET DIVISIONS
# -----------------------
@studCheck.route("/divisions/<course_id>/<int:sem>")
def get_divisions(course_id, sem):
    if divisions.empty:
        return jsonify({"error": "Divisions data not available"}), 500

    data = divisions[
        (divisions["course_id"].astype(str) == str(course_id)) &
        (divisions["semester"] == sem)
    ]

    return jsonify(data.to_dict(orient="records"))