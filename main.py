import sys
import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from datetime import datetime

# Robust path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "website"))

# Now we can import from the website folder as if it were top-level
try:
    from website.routes import (
        classroom_router,
        subject_router,
        faculty_router,
        student_router,
        timing_router,
        timetable_router,
        load_data_router
    )
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    # Fallback to prevent crash during import
    classroom_router = subject_router = faculty_router = student_router = timing_router = timetable_router = load_data_router = None

MONGO_URI = os.getenv("MONGO_URI", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
DATABASE_NAME = os.getenv("MONGO_DB_NAME", "edusched")

db_client = None
database = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, database
    try:
        db_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        database = db_client[DATABASE_NAME]
        app.state.db = database
        # Verify connection
        await database.command('ping')
        print(f"[OK] Connected to MongoDB: {DATABASE_NAME}")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
    
    yield
    
    if db_client:
        db_client.close()
    print("[OK] Disconnected from MongoDB")

app = FastAPI(
    title="University Timetable Generation System - Pro",
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

# Include routers if they were imported successfully
if classroom_router:
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
        if app.state.db is None:
            raise Exception("Database not initialized")
        await app.state.db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "db_name": DATABASE_NAME,
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

@app.get("/api/debug")
async def debug_info():
    return {
        "base_dir": BASE_DIR,
        "sys_path": sys.path[:5],
        "env_mongo_uri_set": "MONGO_URI" in os.environ or "MONGODB_URL" in os.environ,
        "database_name": DATABASE_NAME,
        "index_exists": os.path.exists(os.path.join(BASE_DIR, "website", "templates", "index.html"))
    }

@app.get("/")
async def serve_ui():
    html_path = os.path.join(BASE_DIR, "website", "templates", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return JSONResponse(
        status_code=404, 
        content={"message": f"Frontend not found. Looked at: {html_path}"}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": type(exc).__name__, "message": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)