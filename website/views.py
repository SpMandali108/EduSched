from flask import Blueprint ,render_template

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template("index.html")


@views.route('/student-dashboard')
def student_dashboard():
    return render_template("index.html")


@views.route('/timetable-ui')
def timetable_ui():
    return render_template("index.html")