from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
import os


load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("key")
    mongo_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    mongo_db_name = os.environ.get("TIMETABLE_DB_NAME", "university_timetable_pro")
    mongo_client = MongoClient(mongo_url)
    app.config["MONGO_CLIENT"] = mongo_client
    app.config["MONGO_DB"] = mongo_client[mongo_db_name]

    from .views import views
    from .studCheck import studCheck  
    # from .timeTable import timeTable
    from .facultyPreference import facultyPreference
    from .facultyProfile import facultyProfile
    from .timetable_api import timetable_api

    app.register_blueprint(views, url_prefix='/') 
    app.register_blueprint(studCheck, url_prefix='/')
    # app.register_blueprint(timeTable, url_prefix='/')
    app.register_blueprint(facultyPreference, url_prefix='/')
    app.register_blueprint(facultyProfile, url_prefix='/')
    app.register_blueprint(timetable_api, url_prefix='/')

   
    return app