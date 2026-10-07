import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from backend.config import settings
from backend.database.session import Base, engine, ensure_schema
from backend.api import projects, scenes, shots, clips, jobs, ai, system
from backend.logging_config import api_logger

# Initialize database schema and migrate columns
ensure_schema()

app = FastAPI(
    title="AI Movie Studio API",
    description="Full-stack AI Movie Studio for Kaggle NVIDIA T4 (16GB VRAM) with OpenRouter & CogVideoX",
    version="1.0.0"
)

# Enable CORS for frontend Vite dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(projects.router)
app.include_router(scenes.router)
app.include_router(shots.router)
app.include_router(clips.router)
app.include_router(jobs.router)
app.include_router(ai.router)
app.include_router(system.router)

# Mount outputs and projects directories for video streaming and asset previews
outputs_path = Path(settings.OUTPUT_DIR)
outputs_path.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(outputs_path)), name="outputs")

projects_path = Path(settings.PROJECTS_DIR)
projects_path.mkdir(parents=True, exist_ok=True)
app.mount("/projects-media", StaticFiles(directory=str(projects_path)), name="projects_media")

# Serve frontend build if present (e.g. on Kaggle or production deployment)
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_candidate = frontend_dist / full_path
        if file_candidate.exists() and file_candidate.is_file():
            return FileResponse(file_candidate)
        return FileResponse(frontend_dist / "index.html")

@app.on_event("startup")
async def startup_event():
    api_logger.info("AI Movie Studio Backend initialized.")

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    api_logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "path": request.url.path}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
