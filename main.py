import sys
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from datetime import datetime

# Add website directory to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "website"))

from website.routes import (
    classroom_router,
    subject_router,
    faculty_router,
    student_router,
    timing_router,
    timetable_router,
    load_data_router
)

MONGO_URI = os.getenv("MONGO_URI", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
DATABASE_NAME = os.getenv("MONGO_DB_NAME", "edusched")

db_client = None
database = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, database
    db_client = AsyncIOMotorClient(MONGO_URI)
    database = db_client[DATABASE_NAME]
    app.state.db = database
    print(f"[OK] Connected to MongoDB: {DATABASE_NAME}")
    
    yield
    
    db_client.close()
    print("[OK] Disconnected from MongoDB")

app = FastAPI(
    title="University Timetable Generation System - Pro",
    description="Production-ready automated timetable generation with constraint solving",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(classroom_router, prefix="/api/classrooms", tags=["Classrooms"])
app.include_router(subject_router, prefix="/api/subjects", tags=["Subjects"])
app.include_router(faculty_router, prefix="/api/faculty", tags=["Faculty"])
app.include_router(student_router, prefix="/api/students", tags=["Students"])
app.include_router(timing_router, prefix="/api/timings", tags=["Timings"])
app.include_router(timetable_router, prefix="/api/timetable", tags=["Timetable"])
app.include_router(load_data_router, prefix="/api/load-data", tags=["Load Data"])

@app.get("/api/health")
async def health_check():
    try:
        await app.state.db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/")
def serve_ui():
    html_path = os.path.join(os.path.dirname(__file__), "website", "templates", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse(status_code=404, content={"message": f"Frontend not found at {html_path}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)