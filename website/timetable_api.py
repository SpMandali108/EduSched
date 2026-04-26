"""
Flask routes converted from Smit's FastAPI module.
"""

from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from pymongo.errors import PyMongoError

from .load_sample_data import load_assignment_data, load_sample_data
from .timetable_generator import TimetableGenerator

timetable_api = Blueprint("timetable_api", __name__)


def _db():
    return current_app.config["MONGO_DB"]


def _clean(doc):
    if not doc:
        return doc
    out = dict(doc)
    out.pop("_id", None)
    return out


def _json_or_empty():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _upsertable(collection, key_name, key_value, create_message, update_message):
    payload = _json_or_empty()
    if not payload:
        return jsonify({"error": "Request body required"}), 400
    payload[key_name] = key_value
    existing = _db()[collection].find_one({key_name: key_value})
    if existing:
        _db()[collection].update_one({key_name: key_value}, {"$set": payload})
        return jsonify({"message": update_message, key_name: key_value})
    _db()[collection].insert_one(payload)
    return jsonify({"message": create_message, key_name: key_value}), 201


def _auto_regenerate():
    generator = TimetableGenerator(_db())
    result = generator.generate({"force_regenerate": True})
    return result


@timetable_api.route("/api/health", methods=["GET"])
def health_check():
    try:
        _db().command("ping")
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as exc:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(exc)}), 503


@timetable_api.route("/api/load-sample-data", methods=["POST"])
def load_sample_data_api():
    try:
        base_dir = Path(current_app.root_path).parent / "data"
        stats = load_sample_data(_db(), base_dir)
        return jsonify({"success": True, "message": "Sample data loaded", "stats": stats})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@timetable_api.route("/api/sync-faculty-assignment", methods=["POST"])
def sync_faculty_assignment_api():
    """
    Sync latest faculty-assignment output into timetable collections.

    FIX: Previously used get_filtered_assignments() which only fetched one
    semester type (odd OR even), causing practical subjects from the other
    semester to be completely missing from the generated timetable.
    Now uses get_all_assignments() to include both odd and even semesters.

    Supports optional filtering via JSON body: { "sem": "odd"|"even",
    "dept": "CSE", "course": "CSE_UG", "generate": true }.
    If "sem" is omitted, ALL assignments (odd + even) are synced.
    """
    try:
        from .facultyPreference import get_all_assignments, get_filtered_assignments

        payload = _json_or_empty()
        should_generate = payload.get("generate", True)
        sem_type = payload.get("sem", "")      # empty = both semesters
        dept = payload.get("dept", "")
        course = payload.get("course", "")

        # FIX: When no sem_type filter is given, pull both odd and even so that
        # practical subjects from every semester are included.
        if sem_type:
            assignments = get_filtered_assignments(sem_type, dept, course)
        else:
            assignments = get_all_assignments()
            # Apply optional dept / course filters after combining
            dept_upper = (dept or "").strip().upper()
            course_upper = (course or "").strip().upper()
            if dept_upper:
                assignments = [a for a in assignments
                               if str(a.get("department", "")).upper() == dept_upper]
            if course_upper:
                assignments = [a for a in assignments
                               if course_upper in str(a.get("course_id", "")).upper()]

        stats = load_assignment_data(_db(), Path(current_app.root_path).parent / "data", assignments)

        response = {
            "message": "Faculty assignment synced to timetable data",
            "stats": stats,
        }

        if should_generate:
            generator = TimetableGenerator(_db())
            response["generation"] = generator.generate({"force_regenerate": True})

        response["success"] = True
        return jsonify(response)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@timetable_api.route("/api/reset-data", methods=["POST"])
def reset_data_api():
    try:
        _db().classrooms.delete_many({})
        _db().subjects.delete_many({})
        _db().faculty.delete_many({})
        _db().student_groups.delete_many({})
        _db().timing_config.delete_many({})
        _db().timetables.delete_many({})
        return jsonify({"success": True, "message": "All university data has been cleared"})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@timetable_api.route("/api/classrooms", methods=["GET", "POST"])
def classrooms():
    if request.method == "GET":
        rows = [_clean(row) for row in _db().classrooms.find({})]
        return jsonify({"classrooms": rows, "count": len(rows)})
    payload = _json_or_empty()
    classroom_id = payload.get("classroom_id")
    if not classroom_id:
        return jsonify({"error": "classroom_id is required"}), 400
    if _db().classrooms.find_one({"classroom_id": classroom_id}):
        return jsonify({"error": "Classroom already exists"}), 400
    _db().classrooms.insert_one(payload)
    _auto_regenerate()
    return jsonify({"message": "Classroom created successfully", "classroom_id": classroom_id}), 201


@timetable_api.route("/api/classrooms/<classroom_id>", methods=["GET", "PUT", "DELETE"])
def classroom_by_id(classroom_id):
    if request.method == "GET":
        row = _clean(_db().classrooms.find_one({"classroom_id": classroom_id}))
        return (jsonify(row), 200) if row else (jsonify({"error": "Classroom not found"}), 404)
    if request.method == "PUT":
        payload = _json_or_empty()
        if not payload:
            return jsonify({"error": "No data to update"}), 400
        result = _db().classrooms.update_one({"classroom_id": classroom_id}, {"$set": payload})
        if result.matched_count == 0:
            return jsonify({"error": "Classroom not found"}), 404
        _auto_regenerate()
        return jsonify({"message": "Classroom updated successfully"})
    result = _db().classrooms.delete_one({"classroom_id": classroom_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Classroom not found"}), 404
    _auto_regenerate()
    return jsonify({"message": "Classroom deleted successfully"})


@timetable_api.route("/api/subjects", methods=["GET", "POST"])
def subjects():
    if request.method == "GET":
        branch = request.args.get("branch")
        semester = request.args.get("semester", type=int)
        query = {}
        if branch:
            query["branch"] = branch
        if semester:
            query["semester"] = semester
        rows = [_clean(row) for row in _db().subjects.find(query)]
        return jsonify({"subjects": rows, "count": len(rows)})
    payload = _json_or_empty()
    subject_code = payload.get("subject_code")
    if not subject_code:
        return jsonify({"error": "subject_code is required"}), 400
    if _db().subjects.find_one({"subject_code": subject_code}):
        return jsonify({"error": "Subject already exists"}), 400
    _db().subjects.insert_one(payload)
    _auto_regenerate()
    return jsonify({"message": "Subject created successfully", "subject_code": subject_code}), 201


@timetable_api.route("/api/subjects/<subject_code>", methods=["GET", "PUT", "DELETE"])
def subject_by_code(subject_code):
    if request.method == "GET":
        row = _clean(_db().subjects.find_one({"subject_code": subject_code}))
        return (jsonify(row), 200) if row else (jsonify({"error": "Subject not found"}), 404)
    if request.method == "PUT":
        payload = _json_or_empty()
        if not payload:
            return jsonify({"error": "No data to update"}), 400
        result = _db().subjects.update_one({"subject_code": subject_code}, {"$set": payload})
        if result.matched_count == 0:
            return jsonify({"error": "Subject not found"}), 404
        _auto_regenerate()
        return jsonify({"message": "Subject updated successfully"})
    result = _db().subjects.delete_one({"subject_code": subject_code})
    if result.deleted_count == 0:
        return jsonify({"error": "Subject not found"}), 404
    _auto_regenerate()
    return jsonify({"message": "Subject deleted successfully"})


@timetable_api.route("/api/faculty", methods=["GET", "POST"])
def faculty():
    if request.method == "GET":
        rows = [_clean(row) for row in _db().faculty.find({})]
        return jsonify({"faculty": rows, "count": len(rows)})
    payload = _json_or_empty()
    faculty_id = payload.get("faculty_id")
    if not faculty_id:
        return jsonify({"error": "faculty_id is required"}), 400
    if _db().faculty.find_one({"faculty_id": faculty_id}):
        return jsonify({"error": "Faculty already exists"}), 400
    _db().faculty.insert_one(payload)
    _auto_regenerate()
    return jsonify({"message": "Faculty created successfully", "faculty_id": faculty_id}), 201


@timetable_api.route("/api/faculty/<faculty_id>", methods=["GET", "PUT", "DELETE"])
def faculty_by_id(faculty_id):
    if request.method == "GET":
        row = _clean(_db().faculty.find_one({"faculty_id": faculty_id}))
        return (jsonify(row), 200) if row else (jsonify({"error": "Faculty not found"}), 404)
    if request.method == "PUT":
        payload = _json_or_empty()
        if not payload:
            return jsonify({"error": "No data to update"}), 400
        result = _db().faculty.update_one({"faculty_id": faculty_id}, {"$set": payload})
        if result.matched_count == 0:
            return jsonify({"error": "Faculty not found"}), 404
        _auto_regenerate()
        return jsonify({"message": "Faculty updated successfully"})
    result = _db().faculty.delete_one({"faculty_id": faculty_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Faculty not found"}), 404
    _auto_regenerate()
    return jsonify({"message": "Faculty deleted successfully"})


@timetable_api.route("/api/students", methods=["GET", "POST"])
def students():
    if request.method == "GET":
        rows = [_clean(row) for row in _db().student_groups.find({})]
        return jsonify({"student_groups": rows, "count": len(rows)})
    payload = _json_or_empty()
    branch = payload.get("branch")
    semester = payload.get("semester")
    divisions = payload.get("divisions", [])
    if not branch or not semester or not divisions:
        return jsonify({"error": "branch, semester and divisions are required"}), 400
    group_id = f"{branch}_SEM{semester}"
    if _db().student_groups.find_one({"group_id": group_id}):
        return jsonify({"error": "Student group already exists"}), 400
    payload["group_id"] = group_id
    _db().student_groups.insert_one(payload)
    _auto_regenerate()
    return jsonify({"message": "Student group created successfully", "group_id": group_id}), 201


@timetable_api.route("/api/students/<group_id>", methods=["GET", "PUT", "DELETE"])
def student_by_group(group_id):
    if request.method == "GET":
        row = _clean(_db().student_groups.find_one({"group_id": group_id}))
        return (jsonify(row), 200) if row else (jsonify({"error": "Student group not found"}), 404)
    if request.method == "PUT":
        payload = _json_or_empty()
        if not payload:
            return jsonify({"error": "No data to update"}), 400
        result = _db().student_groups.update_one({"group_id": group_id}, {"$set": payload})
        if result.matched_count == 0:
            return jsonify({"error": "Student group not found"}), 404
        _auto_regenerate()
        return jsonify({"message": "Student group updated successfully"})
    result = _db().student_groups.delete_one({"group_id": group_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Student group not found"}), 404
    _auto_regenerate()
    return jsonify({"message": "Student group deleted successfully"})


@timetable_api.route("/api/timings", methods=["GET", "POST", "PUT"])
def timings():
    if request.method == "GET":
        row = _clean(_db().timing_config.find_one({"config_id": "default"}))
        return (jsonify(row), 200) if row else (jsonify({"error": "Timing configuration not found"}), 404)
    payload = _json_or_empty()
    if not payload:
        return jsonify({"error": "Request body required"}), 400
    payload["config_id"] = "default"
    _db().timing_config.update_one({"config_id": "default"}, {"$set": payload}, upsert=True)
    _auto_regenerate()
    return jsonify({"message": "Timing configuration saved successfully"})


@timetable_api.route("/api/timetable/generate", methods=["POST"])
def generate_timetable():
    params = _json_or_empty()
    try:
        generator = TimetableGenerator(_db())
        return jsonify(generator.generate(params))
    except PyMongoError as exc:
        return jsonify({"error": f"Database error: {str(exc)})"}), 500
    except Exception as exc:
        return jsonify({"error": f"Timetable generation failed: {str(exc)}"}), 500


@timetable_api.route("/api/timetable", methods=["GET", "DELETE"])
def all_timetables():
    if request.method == "GET":
        entity_type = request.args.get("entity_type")
        query = {"entity_type": entity_type} if entity_type else {}
        rows = [_clean(row) for row in _db().timetables.find(query)]
        return jsonify({"timetables": rows, "count": len(rows)})
    result = _db().timetables.delete_many({})
    return jsonify({"message": f"Deleted {result.deleted_count} timetables"})


@timetable_api.route("/api/timetable/<timetable_id>", methods=["GET", "DELETE"])
def timetable_by_id(timetable_id):
    if request.method == "GET":
        row = _clean(_db().timetables.find_one({"timetable_id": timetable_id}))
        return (jsonify(row), 200) if row else (jsonify({"error": "Timetable not found"}), 404)
    result = _db().timetables.delete_one({"timetable_id": timetable_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Timetable not found"}), 404
    return jsonify({"message": "Timetable deleted successfully"})


@timetable_api.route("/api/timetable/<timetable_id>/edit", methods=["PUT"])
def edit_timetable(timetable_id):
    """Edit a specific timetable entry"""
    payload = _json_or_empty()
    day = payload.get("day")
    slot_id = payload.get("slot_id")
    if not day or not slot_id:
        return jsonify({"error": "day and slot_id are required"}), 400

    update_fields = {}
    for k in ["subject_code", "faculty_id", "classroom_id", "entry_type"]:
        if k in payload:
            update_fields[f"entries.$.{k}"] = payload[k]

    if not update_fields:
        return jsonify({"error": "No fields to update"}), 400

    result = _db().timetables.update_one(
        {
            "timetable_id": timetable_id,
            "entries.day": day,
            "entries.slot_id": slot_id
        },
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Timetable entry not found"}), 404

    return jsonify({"message": "Timetable entry updated successfully"})