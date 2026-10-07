from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from backend.database.session import get_db
from backend.models.db import Shot, Scene, Clip, Project
from backend.schemas.api import ShotCreate, ShotResponse, BreakIntoClipsRequest, EnhancePromptRequest
from backend.services.ai.director import AIDirector
from backend.logging_config import api_logger

router = APIRouter(tags=["shots"])
ai_director = AIDirector()

@router.get("/api/scenes/{scene_id}/shots", response_model=List[ShotResponse])
def list_shots(scene_id: str, db: Session = Depends(get_db)):
    return db.query(Shot).filter(Shot.scene_id == scene_id).order_by(Shot.shot_number).all()

@router.post("/api/scenes/{scene_id}/shots", response_model=ShotResponse)
def create_shot(scene_id: str, data: ShotCreate, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    shot = Shot(
        scene_id=scene_id,
        shot_number=data.shot_number,
        description=data.description or "",
        reference_image=data.reference_image or "",
        image_prompt=data.image_prompt or "",
        video_prompt=data.video_prompt or "",
        camera_motion=data.camera_motion or "Slow smooth camera move",
        subject_motion=data.subject_motion or "Subtle cinematic movement",
        duration=data.duration,
        clip_count=data.clip_count,
        status="Draft"
    )
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return shot

@router.get("/api/shots/{shot_id}", response_model=ShotResponse)
def get_shot(shot_id: str, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot

@router.put("/api/shots/{shot_id}", response_model=ShotResponse)
def update_shot(shot_id: str, data: ShotCreate, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    shot.description = data.description
    shot.reference_image = data.reference_image
    shot.image_prompt = data.image_prompt
    shot.video_prompt = data.video_prompt
    shot.camera_motion = data.camera_motion
    shot.subject_motion = data.subject_motion
    shot.duration = data.duration
    shot.clip_count = data.clip_count

    db.commit()
    db.refresh(shot)
    return shot

@router.delete("/api/shots/{shot_id}")
def delete_shot(shot_id: str, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    db.delete(shot)
    db.commit()
    return {"message": "Shot deleted"}

@router.post("/api/shots/{shot_id}/break-into-clips")
def break_shot_into_clips(shot_id: str, req: BreakIntoClipsRequest, db: Session = Depends(get_db)):
    """
    Core AI Director feature:
    Intelligently decomposes a shot or action prompt into sequential, connected clips
    using OpenRouter and outputs a structured ClipContinuityPlan.
    """
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    scene = db.query(Scene).filter(Scene.id == shot.scene_id).first()
    project = db.query(Project).filter(Project.id == scene.project_id).first() if scene else None

    # Compact AI Context (#11)
    movie_bible_str = project.movie_bible if project and project.movie_bible else ""
    scene_str = f"Scene {scene.scene_number}: {scene.title}. Weather: {scene.weather}. Time: {scene.time_of_day}" if scene else ""

    api_logger.info(f"Breaking shot {shot_id} into {req.clip_count} sequential clips.")
    plan = ai_director.break_into_clips(
        scene_description=req.prompt or shot.description,
        clip_count=req.clip_count,
        duration_per_clip=req.duration_per_clip,
        movie_bible_context=movie_bible_str,
        character_context=scene.characters_json if scene else "",
        location_context=scene.location_name if scene else ""
    )

    # Calculate starting timeline_order
    max_order = db.query(Clip).filter(Clip.project_id == project.id).count() if project else 0

    # Delete existing draft clips for this shot to replace with new plan
    db.query(Clip).filter(Clip.shot_id == shot.id, Clip.preview_status == "Draft").delete()

    created_clips = []
    for idx, c_item in enumerate(plan.clips):
        clip = Clip(
            shot_id=shot.id,
            scene_id=scene.id if scene else "",
            project_id=project.id if project else "",
            clip_number=c_item.clip_number,
            timeline_order=max_order + idx + 1,
            description=c_item.description,
            reference_image=shot.reference_image or "",
            image_prompt=c_item.image_prompt,
            video_prompt=c_item.video_prompt,
            camera_motion=c_item.camera_motion,
            subject_motion=c_item.subject_motion,
            duration=c_item.duration_seconds,
            continuity_from_previous=c_item.continuity_from_previous,
            continuity_to_next=c_item.continuity_to_next,
            preview_status="Draft",
            final_status="Draft",
            prompt_history=json.dumps([{"version": 1, "image": c_item.image_prompt, "video": c_item.video_prompt}])
        )
        db.add(clip)
        created_clips.append(clip)

    shot.clip_count = len(plan.clips)
    shot.description = req.prompt or shot.description
    db.commit()

    return {
        "status": "success",
        "clip_count": len(plan.clips),
        "clips": [
            {
                "id": c.id,
                "clip_number": c.clip_number,
                "description": c.description,
                "image_prompt": c.image_prompt,
                "video_prompt": c.video_prompt,
                "duration": c.duration,
                "continuity_from_previous": c.continuity_from_previous,
                "continuity_to_next": c.continuity_to_next
            }
            for c in created_clips
        ]
    }

@router.post("/api/shots/{shot_id}/enhance")
def enhance_shot_prompt(shot_id: str, req: EnhancePromptRequest, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    scene = db.query(Scene).filter(Scene.id == shot.scene_id).first()
    context = f"Scene {scene.title if scene else ''}, Shot {shot.shot_number}"
    res = ai_director.enhance_prompt(req.prompt or shot.description, req.prompt_type, context)
    return res.model_dump()
