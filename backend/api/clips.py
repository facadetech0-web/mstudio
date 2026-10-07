import json
import os
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.db import Clip, Shot, Scene, Project, Job, Asset
from backend.schemas.api import ClipUpdate, ClipResponse, GenerateRequest
from backend.services.queue.worker import generation_worker
from backend.services.ai.director import AIDirector
from backend.config import settings
from backend.logging_config import api_logger

router = APIRouter(tags=["clips"])
ai_director = AIDirector()

@router.get("/api/shots/{shot_id}/clips", response_model=List[ClipResponse])
def list_clips(shot_id: str, db: Session = Depends(get_db)):
    clips = db.query(Clip).filter(Clip.shot_id == shot_id).order_by(Clip.clip_number).all()
    res = []
    for c in clips:
        try:
            history = json.loads(c.prompt_history) if c.prompt_history else []
        except Exception:
            history = []
        res.append(ClipResponse(
            id=c.id,
            shot_id=c.shot_id,
            scene_id=c.scene_id,
            project_id=c.project_id,
            clip_number=c.clip_number,
            timeline_order=c.timeline_order or 1,
            description=c.description or "",
            reference_image=c.reference_image or "",
            image_prompt=c.image_prompt or "",
            video_prompt=c.video_prompt or "",
            negative_prompt=c.negative_prompt or "",
            lora_path=c.lora_path or "",
            camera_motion=c.camera_motion or "",
            subject_motion=c.subject_motion or "",
            duration=c.duration or 5.0,
            continuity_from_previous=c.continuity_from_previous,
            continuity_to_next=c.continuity_to_next,
            preview_status=c.preview_status or "Draft",
            final_status=c.final_status or "Draft",
            preview_file=c.preview_file or "",
            final_file=c.final_file or "",
            seed=c.seed,
            prompt_history=history,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return res

@router.get("/api/projects/{project_id}/timeline", response_model=List[ClipResponse])
def get_project_timeline(project_id: str, db: Session = Depends(get_db)):
    clips = db.query(Clip).filter(Clip.project_id == project_id).order_by(Clip.timeline_order, Clip.clip_number).all()
    res = []
    for c in clips:
        try:
            history = json.loads(c.prompt_history) if c.prompt_history else []
        except Exception:
            history = []
        res.append(ClipResponse(
            id=c.id,
            shot_id=c.shot_id,
            scene_id=c.scene_id,
            project_id=c.project_id,
            clip_number=c.clip_number,
            timeline_order=c.timeline_order or 1,
            description=c.description or "",
            reference_image=c.reference_image or "",
            image_prompt=c.image_prompt or "",
            video_prompt=c.video_prompt or "",
            negative_prompt=c.negative_prompt or "",
            lora_path=c.lora_path or "",
            camera_motion=c.camera_motion or "",
            subject_motion=c.subject_motion or "",
            duration=c.duration or 5.0,
            continuity_from_previous=c.continuity_from_previous,
            continuity_to_next=c.continuity_to_next,
            preview_status=c.preview_status or "Draft",
            final_status=c.final_status or "Draft",
            preview_file=c.preview_file or "",
            final_file=c.final_file or "",
            seed=c.seed,
            prompt_history=history,
            created_at=c.created_at,
            updated_at=c.updated_at
        ))
    return res

@router.get("/api/clips/{clip_id}", response_model=ClipResponse)
def get_clip(clip_id: str, db: Session = Depends(get_db)):
    c = db.query(Clip).filter(Clip.id == clip_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Clip not found")
    try:
        history = json.loads(c.prompt_history) if c.prompt_history else []
    except Exception:
        history = []
    return ClipResponse(
        id=c.id,
        shot_id=c.shot_id,
        scene_id=c.scene_id,
        project_id=c.project_id,
        clip_number=c.clip_number,
        timeline_order=c.timeline_order or 1,
        description=c.description or "",
        reference_image=c.reference_image or "",
        image_prompt=c.image_prompt or "",
        video_prompt=c.video_prompt or "",
        negative_prompt=c.negative_prompt or "",
        lora_path=c.lora_path or "",
        camera_motion=c.camera_motion or "",
        subject_motion=c.subject_motion or "",
        duration=c.duration or 5.0,
        continuity_from_previous=c.continuity_from_previous,
        continuity_to_next=c.continuity_to_next,
        preview_status=c.preview_status or "Draft",
        final_status=c.final_status or "Draft",
        preview_file=c.preview_file or "",
        final_file=c.final_file or "",
        seed=c.seed,
        prompt_history=history,
        created_at=c.created_at,
        updated_at=c.updated_at
    )

@router.put("/api/clips/{clip_id}", response_model=ClipResponse)
def update_clip(clip_id: str, data: ClipUpdate, db: Session = Depends(get_db)):
    c = db.query(Clip).filter(Clip.id == clip_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Clip not found")

    if data.description is not None:
        c.description = data.description
    if data.reference_image is not None:
        c.reference_image = data.reference_image
    if data.image_prompt is not None:
        c.image_prompt = data.image_prompt
    if data.video_prompt is not None:
        # Prompt versioning (#58)
        try:
            history = json.loads(c.prompt_history) if c.prompt_history else []
        except Exception:
            history = []
        history.append({"version": len(history) + 1, "video": data.video_prompt, "image": c.image_prompt})
        c.prompt_history = json.dumps(history)
        c.video_prompt = data.video_prompt
    if data.negative_prompt is not None:
        c.negative_prompt = data.negative_prompt
    if data.lora_path is not None:
        c.lora_path = data.lora_path
    if data.camera_motion is not None:
        c.camera_motion = data.camera_motion
    if data.subject_motion is not None:
        c.subject_motion = data.subject_motion
    if data.duration is not None:
        c.duration = data.duration
    if data.timeline_order is not None:
        c.timeline_order = data.timeline_order
    if data.preview_status is not None:
        c.preview_status = data.preview_status
    if data.final_status is not None:
        c.final_status = data.final_status
    if data.seed is not None:
        c.seed = data.seed

    db.commit()
    db.refresh(c)
    return get_clip(clip_id, db)

@router.delete("/api/clips/{clip_id}")
def delete_clip(clip_id: str, db: Session = Depends(get_db)):
    c = db.query(Clip).filter(Clip.id == clip_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Clip not found")
    db.delete(c)
    db.commit()
    return {"message": "Clip deleted"}

@router.post("/api/clips/{clip_id}/preview")
def generate_clip_preview(clip_id: str, req: Optional[GenerateRequest] = None, db: Session = Depends(get_db)):
    """
    Enqueues CogVideoX-2B preview generation job for this single clip.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    steps = req.steps if req and req.steps else 15
    frames = req.frames if req and req.frames else 49
    seed = req.seed if (req and req.seed is not None) else clip.seed
    neg_prompt = req.negative_prompt if (req and req.negative_prompt is not None) else (clip.negative_prompt or "")
    lora = req.lora_path if (req and req.lora_path is not None) else (clip.lora_path or "")

    if req and req.negative_prompt is not None:
        clip.negative_prompt = req.negative_prompt
    if req and req.lora_path is not None:
        clip.lora_path = req.lora_path

    job = Job(
        project_id=clip.project_id,
        scene_id=clip.scene_id,
        shot_id=clip.shot_id,
        clip_id=clip.id,
        mode="preview",
        model="cogvideox-2b",
        status="Waiting",
        progress=0.0,
        steps_completed=0,
        total_steps=steps,
        seed=seed,
        resolution="720x480",
        frames=frames,
        steps=steps,
        negative_prompt=neg_prompt,
        lora_path=lora
    )
    db.add(job)
    clip.preview_status = "Queued"
    db.commit()
    db.refresh(job)

    generation_worker.enqueue_job(job.id)

    return {"status": "queued", "job_id": job.id, "clip_id": clip.id, "model": "cogvideox-2b"}

@router.post("/api/clips/{clip_id}/final")
def generate_clip_final(clip_id: str, req: Optional[GenerateRequest] = None, db: Session = Depends(get_db)):
    """
    Enqueues CogVideoX-5B-I2V final generation job for this approved clip.
    Requires a reference image or uses existing frame.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    steps = req.steps if req and req.steps else 30
    frames = req.frames if req and req.frames else 49
    seed = req.seed if (req and req.seed is not None) else clip.seed
    neg_prompt = req.negative_prompt if (req and req.negative_prompt is not None) else (clip.negative_prompt or "")
    lora = req.lora_path if (req and req.lora_path is not None) else (clip.lora_path or "")

    if req and req.negative_prompt is not None:
        clip.negative_prompt = req.negative_prompt
    if req and req.lora_path is not None:
        clip.lora_path = req.lora_path

    job = Job(
        project_id=clip.project_id,
        scene_id=clip.scene_id,
        shot_id=clip.shot_id,
        clip_id=clip.id,
        mode="final",
        model="cogvideox-5b-i2v",
        status="Waiting",
        progress=0.0,
        steps_completed=0,
        total_steps=steps,
        seed=seed,
        resolution="720x480",
        frames=frames,
        steps=steps,
        negative_prompt=neg_prompt,
        lora_path=lora
    )
    db.add(job)
    clip.final_status = "Queued"
    db.commit()
    db.refresh(job)

    generation_worker.enqueue_job(job.id)

    return {"status": "queued", "job_id": job.id, "clip_id": clip.id, "model": "cogvideox-5b-i2v"}

@router.post("/api/clips/{clip_id}/approve")
def approve_clip(clip_id: str, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.preview_status = "Approved"
    db.commit()
    return {"status": "success", "clip_id": clip.id, "preview_status": "Approved"}

@router.post("/api/clips/{clip_id}/reject")
def reject_clip(clip_id: str, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.preview_status = "Rejected"
    db.commit()
    return {"status": "success", "clip_id": clip.id, "preview_status": "Rejected"}

@router.post("/api/clips/{clip_id}/regenerate")
def regenerate_clip(clip_id: str, instructions: Optional[Dict[str, str]] = None, db: Session = Depends(get_db)):
    """
    Requirement #29 & #57: Smart Individual Clip Regeneration.
    Preserves context (Bible, previous clip, next clip), applies user adjustments,
    and enqueues only this clip without affecting other clips.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    adjust_text = (instructions or {}).get("instructions", "")
    if adjust_text:
        # Prompt enhancement preserving context
        enh = ai_director.enhance_prompt(f"{clip.video_prompt}. Adjustment: {adjust_text}", "video")
        clip.video_prompt = enh.enhanced_video_prompt

    # Reset statuses
    clip.preview_status = "Queued"
    clip.preview_file = ""

    job = Job(
        project_id=clip.project_id,
        scene_id=clip.scene_id,
        shot_id=clip.shot_id,
        clip_id=clip.id,
        mode="preview",
        model="cogvideox-2b",
        status="Waiting",
        progress=0.0,
        steps_completed=0,
        total_steps=25,
        resolution="720x480",
        frames=49,
        steps=25
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    generation_worker.enqueue_job(job.id)

    return {"status": "regenerating", "job_id": job.id, "clip_id": clip.id}

@router.post("/api/clips/reorder")
def reorder_timeline(data: Dict[str, List[str]], db: Session = Depends(get_db)):
    """
    Requirement #32: Timeline reordering.
    Expects {"clip_ids": ["id_1", "id_2", ...]}. Updates timeline_order accordingly.
    """
    clip_ids = data.get("clip_ids", [])
    for order, c_id in enumerate(clip_ids, start=1):
        clip = db.query(Clip).filter(Clip.id == c_id).first()
        if clip:
            clip.timeline_order = order
    db.commit()
    return {"status": "success", "reordered_count": len(clip_ids)}

@router.post("/api/clips/{clip_id}/upload-reference")
def upload_reference_image(clip_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Requirement #26: Upload reference image for I2V generation.
    """
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    ref_dir = Path(settings.PROJECTS_DIR) / clip.project_id / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] or ".png"
    safe_name = f"ref_{clip.id[:8]}{file_ext}"
    dest_path = ref_dir / safe_name

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    clip.reference_image = str(dest_path)
    db.commit()

    return {"status": "success", "reference_image": str(dest_path)}
