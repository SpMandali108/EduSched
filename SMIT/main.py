"""
University Timetable Generation System - Production Ready Backend
Enhanced version with improved features
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
from datetime import datetime

from routes import (
    classroom_router,
    subject_router,
    faculty_router,
    student_router,
    timing_router,
    timetable_router
)

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "university_timetable_pro"

# Global database client
db_client = None
database = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_client, database
    db_client = AsyncIOMotorClient(MONGODB_URL)
    database = db_client[DATABASE_NAME]
    app.state.db = database
    print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
    
    yield
    
    # Shutdown
    db_client.close()
    print("🔌 Disconnected from MongoDB")

# Initialize FastAPI app
app = FastAPI(
    title="University Timetable Generation System - Pro",
    description="Production-ready automated timetable generation with constraint solving",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware - production ready
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "University Timetable Generation System API - Production Ready",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
