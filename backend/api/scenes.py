import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.db import Scene, Shot, Project, Clip
from backend.schemas.api import SceneCreate, SceneResponse, EnhancePromptRequest
from backend.services.ai.director import AIDirector

router = APIRouter(tags=["scenes"])
ai_director = AIDirector()

@router.get("/api/projects/{project_id}/scenes", response_model=List[SceneResponse])
def list_scenes(project_id: str, db: Session = Depends(get_db)):
    scenes = db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.scene_number).all()
    res = []
    for s in scenes:
        try:
            chars = json.loads(s.characters_json) if s.characters_json else []
        except Exception:
            chars = []
        res.append(SceneResponse(
            id=s.id,
            project_id=s.project_id,
            scene_number=s.scene_number,
            title=s.title,
            description=s.description or "",
            location_id=s.location_id,
            location_name=s.location_name or "",
            characters=chars,
            time_of_day=s.time_of_day or "Day",
            weather=s.weather or "Clear",
            visual_style=s.visual_style or "",
            created_at=s.created_at,
            updated_at=s.updated_at
        ))
    return res

@router.post("/api/projects/{project_id}/scenes", response_model=SceneResponse)
def create_scene(project_id: str, data: SceneCreate, db: Session = Depends(get_db)):
    scene = Scene(
        project_id=project_id,
        scene_number=data.scene_number,
        title=data.title,
        description=data.description or "",
        location_id=data.location_id,
        location_name=data.location_name or "",
        characters_json=json.dumps(data.characters or []),
        time_of_day=data.time_of_day or "Day",
        weather=data.weather or "Clear",
        visual_style=data.visual_style or ""
    )
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return SceneResponse(
        id=scene.id,
        project_id=scene.project_id,
        scene_number=scene.scene_number,
        title=scene.title,
        description=scene.description,
        location_id=scene.location_id,
        location_name=scene.location_name,
        characters=data.characters or [],
        time_of_day=scene.time_of_day,
        weather=scene.weather,
        visual_style=scene.visual_style,
        created_at=scene.created_at,
        updated_at=scene.updated_at
    )

@router.get("/api/scenes/{scene_id}", response_model=SceneResponse)
def get_scene(scene_id: str, db: Session = Depends(get_db)):
    s = db.query(Scene).filter(Scene.id == scene_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scene not found")
    try:
        chars = json.loads(s.characters_json) if s.characters_json else []
    except Exception:
        chars = []
    return SceneResponse(
        id=s.id,
        project_id=s.project_id,
        scene_number=s.scene_number,
        title=s.title,
        description=s.description or "",
        location_id=s.location_id,
        location_name=s.location_name or "",
        characters=chars,
        time_of_day=s.time_of_day or "Day",
        weather=s.weather or "Clear",
        visual_style=s.visual_style or "",
        created_at=s.created_at,
        updated_at=s.updated_at
    )

@router.delete("/api/scenes/{scene_id}")
def delete_scene(scene_id: str, db: Session = Depends(get_db)):
    s = db.query(Scene).filter(Scene.id == scene_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scene not found")
    db.delete(s)
    db.commit()
    return {"message": "Scene deleted"}

@router.post("/api/scenes/{scene_id}/break-into-shots")
def break_scene_into_shots(scene_id: str, db: Session = Depends(get_db)):
    s = db.query(Scene).filter(Scene.id == scene_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scene not found")

    # If shot doesn't exist, create initial default master shot
    shot = Shot(
        scene_id=s.id,
        shot_number=1,
        description=s.description or f"Master shot for {s.title}",
        camera_motion="Slow smooth tracking shot",
        subject_motion="Natural fluid movement",
        duration=5.0,
        clip_count=1,
        status="Draft"
    )
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return {"status": "success", "shot_id": shot.id}

@router.post("/api/scenes/{scene_id}/enhance")
def enhance_scene_prompt(scene_id: str, req: EnhancePromptRequest, db: Session = Depends(get_db)):
    s = db.query(Scene).filter(Scene.id == scene_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scene not found")

    context = f"Scene {s.scene_number}: {s.title}. Location: {s.location_name}. Weather: {s.weather}. Style: {s.visual_style}"
    res = ai_director.enhance_prompt(req.prompt or s.description, req.prompt_type, context)
    return res.model_dump()

@router.post("/api/scenes/{scene_id}/check-continuity")
def check_scene_continuity(scene_id: str, db: Session = Depends(get_db)):
    s = db.query(Scene).filter(Scene.id == scene_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scene not found")

    clips = db.query(Clip).filter(Clip.scene_id == scene_id).order_by(Clip.clip_number).all()
    clips_data = [
        {
            "clip_number": c.clip_number,
            "description": c.description,
            "image_prompt": c.image_prompt,
            "video_prompt": c.video_prompt,
            "continuity_from_previous": c.continuity_from_previous,
            "continuity_to_next": c.continuity_to_next
        }
        for c in clips
    ]

    p = db.query(Project).filter(Project.id == s.project_id).first()
    try:
        bible = json.loads(p.movie_bible) if p and p.movie_bible else {}
    except Exception:
        bible = {}

    report = ai_director.check_continuity(clips_data, bible)
    return report.model_dump()
