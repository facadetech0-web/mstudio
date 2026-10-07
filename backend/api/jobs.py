import json
import queue
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.db import Job
from backend.schemas.api import JobResponse
from backend.services.queue.worker import generation_worker
from backend.logging_config import worker_logger

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("", response_model=List[JobResponse])
def list_jobs(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Job)
    if project_id:
        query = query.filter(Job.project_id == project_id)
    return query.order_by(Job.created_at.desc()).limit(50).all()

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/cancel")
def cancel_job(job_id: str):
    success = generation_worker.cancel_job(job_id)
    return {"status": "success" if success else "already_finished", "job_id": job_id}

@router.post("/{job_id}/retry")
def retry_job(job_id: str, low_vram: bool = False, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "Waiting"
    job.progress = 0.0
    job.error = ""
    job.steps_completed = 0
    if low_vram:
        job.resolution = f"{job.resolution}_low_vram"

    db.commit()
    generation_worker.enqueue_job(job.id)
    return {"status": "re-queued", "job_id": job.id, "low_vram": low_vram}

@router.get("/events/stream")
def stream_job_events():
    """
    Server-Sent Events (SSE) endpoint broadcasting real-time generation updates.
    """
    q = queue.Queue()
    generation_worker.add_subscriber(q)

    def event_generator():
        try:
            # Send initial keepalive
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                try:
                    event = q.get(timeout=20.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Keepalive ping
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        except GeneratorExit:
            pass
        finally:
            generation_worker.remove_subscriber(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
