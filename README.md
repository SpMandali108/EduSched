# 📘 EduSched – Smart Timetable Generator

![GitHub repo size](https://img.shields.io/github/repo-size/your-username/EduSched)
![GitHub stars](https://img.shields.io/github/stars/your-username/EduSched?style=social)
![GitHub forks](https://img.shields.io/github/forks/your-username/EduSched?style=social)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🚀 Overview
EduSched is a web-based timetable generation system designed to automate scheduling for educational institutions.
It uses structured CSV inputs to generate optimized timetables with a simple and clean interface.

---

## ✨ Features

- CSV-based input system (Classroom, Faculty, Subjects, Students)
- Automatic timetable generation
- Clean UI using HTML, CSS, JS (no frameworks)
- Download timetable as image
- Hybrid backend (Flask + FastAPI)
- MongoDB Atlas integration
- Deployed on Render
- No login required

---

## 🏗️ Architecture

Frontend (HTML/CSS/JS)
        │
        ▼
Flask Server (Routing + UI)
        │
        ▼
FastAPI (Timetable Logic)
        │
        ▼
MongoDB Atlas (Database)

---

## ⚙️ Setup

git clone https://github.com/your-username/EduSched.git
cd EduSched

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload --port 8001
python app.py

Open: http://127.0.0.1:5000

---

## 🛠️ Tech Stack

Frontend: HTML, CSS, JS  
Backend: Flask, FastAPI  
Database: MongoDB Atlas  
Deployment: Render  

---

## 👨‍💻 Author
Shashwat Mandali
