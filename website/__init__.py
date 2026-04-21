from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
import os


load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("key")

    from .views import views
    from .studCheck import studCheck  
    # from .timeTable import timeTable
    from .facultyPreference import facultyPreference
    from .facultyProfile import facultyProfile

    app.register_blueprint(views, url_prefix='/') 
    app.register_blueprint(studCheck, url_prefix='/')
    # app.register_blueprint(timeTable, url_prefix='/')
    app.register_blueprint(facultyPreference, url_prefix='/')
    app.register_blueprint(facultyProfile, url_prefix='/')

   
    return app