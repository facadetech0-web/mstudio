import json
import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.db import Project, Scene, Shot, Clip, Character, Location, Job
from backend.schemas.api import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    CharacterCreate, CharacterResponse,
    LocationCreate, LocationResponse,
    ExportRequest, PlanMovieRequest
)
from backend.services.ai.director import AIDirector
from backend.services.ffmpeg.exporter import ffmpeg_exporter
from backend.config import settings
from backend.logging_config import api_logger

router = APIRouter(prefix="/api/projects", tags=["projects"])
ai_director = AIDirector()

@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    res = []
    for p in projects:
        try:
            bible = json.loads(p.movie_bible) if p.movie_bible else {}
        except Exception:
            bible = {}
        res.append(ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description or "",
            genre=p.genre or "Cinematic",
            visual_style=p.visual_style or "",
            movie_bible=bible,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))
    return res

@router.post("", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=data.name,
        description=data.description or "",
        genre=data.genre or "Cinematic",
        visual_style=data.visual_style or "Photorealistic 35mm film",
        movie_bible="{}"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create persistent filesystem folder structure (Requirement #43)
    proj_dir = Path(settings.PROJECTS_DIR) / project.id
    for sub in ["bible", "characters", "locations", "scenes", "exports"]:
        (proj_dir / sub).mkdir(parents=True, exist_ok=True)

    with open(proj_dir / "project.json", "w", encoding="utf-8") as f:
        json.dump({
            "id": project.id,
            "name": project.name,
            "genre": project.genre,
            "visual_style": project.visual_style
        }, f, indent=2)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        genre=project.genre,
        visual_style=project.visual_style,
        movie_bible={},
        created_at=project.created_at,
        updated_at=project.updated_at
    )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        bible = json.loads(p.movie_bible) if p.movie_bible else {}
    except Exception:
        bible = {}

    return ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description or "",
        genre=p.genre or "Cinematic",
        visual_style=p.visual_style or "",
        movie_bible=bible,
        created_at=p.created_at,
        updated_at=p.updated_at
    )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.name is not None:
        p.name = data.name
    if data.description is not None:
        p.description = data.description
    if data.genre is not None:
        p.genre = data.genre
    if data.visual_style is not None:
        p.visual_style = data.visual_style
    if data.movie_bible is not None:
        p.movie_bible = json.dumps(data.movie_bible)

    db.commit()
    db.refresh(p)

    # Persist movie bible to disk
    proj_dir = Path(settings.PROJECTS_DIR) / p.id / "bible"
    proj_dir.mkdir(parents=True, exist_ok=True)
    with open(proj_dir / "movie_bible.json", "w", encoding="utf-8") as f:
        f.write(p.movie_bible)

    try:
        bible = json.loads(p.movie_bible) if p.movie_bible else {}
    except Exception:
        bible = {}

    return ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description or "",
        genre=p.genre or "Cinematic",
        visual_style=p.visual_style or "",
        movie_bible=bible,
        created_at=p.created_at,
        updated_at=p.updated_at
    )

@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(p)
    db.commit()
    return {"message": "Project deleted successfully"}

@router.post("/{project_id}/plan")
def plan_project_with_ai(project_id: str, req: PlanMovieRequest, db: Session = Depends(get_db)):
    """
    OpenRouter AI Director:
    1. Generates complete Movie Bible from high level user idea.
    2. Automatically breaks story into cohesive cinematic scenes.
    3. Populates Characters and Locations libraries.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    api_logger.info(f"AI Director planning movie for project {project_id}: '{req.idea[:60]}'")
    bible = ai_director.generate_movie_bible(req.idea, req.genre or p.genre, req.visual_style or p.visual_style)

    # Save bible
    p.name = bible.title or p.name
    p.description = bible.synopsis or bible.story or req.idea
    p.genre = bible.genre
    p.visual_style = bible.visual_style
    p.movie_bible = json.dumps(bible.model_dump())
    db.commit()

    # Save to disk
    proj_dir = Path(settings.PROJECTS_DIR) / p.id / "bible"
    proj_dir.mkdir(parents=True, exist_ok=True)
    with open(proj_dir / "movie_bible.json", "w", encoding="utf-8") as f:
        f.write(p.movie_bible)

    # Sync characters to database
    db.query(Character).filter(Character.project_id == p.id).delete()
    for char in bible.characters:
        c_model = Character(
            project_id=p.id,
            name=char.name,
            age=char.age,
            gender=char.gender,
            physical_description=char.physical_description,
            face_description=char.face_description,
            hair=char.hair,
            clothing=char.clothing,
            body_type=char.body_type,
            personality=char.personality,
            movement_style=char.movement_style,
            voice_description=char.voice_description,
            continuity_rules=char.continuity_rules
        )
        db.add(c_model)

    # Sync locations to database
    db.query(Location).filter(Location.project_id == p.id).delete()
    for loc in bible.locations:
        l_model = Location(
            project_id=p.id,
            name=loc.name,
            description=loc.description,
            architecture=loc.architecture,
            interior_exterior=loc.interior_exterior,
            lighting=loc.lighting,
            time_of_day=loc.time,
            weather=loc.weather,
            color_mood=loc.color_mood,
            important_objects=loc.important_objects,
            continuity_rules=loc.continuity_rules
        )
        db.add(l_model)

    # Break into scenes (1 to 10 scenes supported)
    scenes_plan = ai_director.break_into_scenes(bible, num_scenes=req.num_scenes or 3)
    # Remove older scenes if regenerating
    db.query(Scene).filter(Scene.project_id == p.id).delete()
    for s_item in scenes_plan.scenes:
        s_model = Scene(
            project_id=p.id,
            scene_number=s_item.scene_number,
            title=s_item.title,
            description=s_item.description,
            location_name=s_item.location_name,
            characters_json=json.dumps(s_item.characters),
            time_of_day=s_item.time_of_day,
            weather=s_item.weather,
            visual_style=s_item.visual_style
        )
        db.add(s_model)

    db.commit()
    db.refresh(p)

    return {
        "status": "success",
        "movie_bible": bible.model_dump(),
        "scenes_created": len(scenes_plan.scenes)
    }

@router.post("/{project_id}/export")
def export_project_movie(project_id: str, req: ExportRequest, db: Session = Depends(get_db)):
    """
    Concatenates approved/ready clips into final movie MP4 using FFmpeg pipeline.
    """
    clips_query = db.query(Clip).filter(Clip.project_id == project_id)
    if req.include_only_approved:
        # Prefer final files if ready, else approved preview files
        clips = clips_query.filter((Clip.preview_status == "Approved") | (Clip.final_status == "Ready")).order_by(Clip.timeline_order).all()
    else:
        clips = clips_query.order_by(Clip.timeline_order).all()

    valid_clip_paths = []
    for c in clips:
        # Use final file if exists, else preview file
        target_path = c.final_file if (c.final_file and os.path.exists(c.final_file)) else c.preview_file
        if target_path and os.path.exists(target_path):
            valid_clip_paths.append(target_path)

    if not valid_clip_paths:
        raise HTTPException(
            status_code=400,
            detail="No rendered video files found for approved clips to export. Please generate and approve clips first."
        )

    export_dir = Path(settings.PROJECTS_DIR) / project_id / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"movie_{project_id[:8]}_{req.resolution}.mp4"
    output_path = str(export_dir / output_filename)

    try:
        result = ffmpeg_exporter.export_movie(
            clip_paths=valid_clip_paths,
            output_path=output_path,
            resolution=req.resolution,
            fps=req.fps
        )
        return {
            "status": "success",
            "message": "Movie successfully exported",
            "output_path": output_path,
            "clips_count": len(valid_clip_paths),
            "file_size_bytes": result["file_size_bytes"]
        }
    except Exception as e:
        api_logger.error(f"Movie export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Characters & Locations endpoints
@router.get("/{project_id}/characters")
def list_characters(project_id: str, db: Session = Depends(get_db)):
    return db.query(Character).filter(Character.project_id == project_id).all()

@router.post("/{project_id}/characters")
def create_character(project_id: str, data: CharacterCreate, db: Session = Depends(get_db)):
    char = Character(
        project_id=project_id,
        name=data.name,
        age=data.age or "",
        gender=data.gender or "",
        physical_description=data.physical_description or "",
        face_description=data.face_description or "",
        hair=data.hair or "",
        clothing=data.clothing or "",
        body_type=data.body_type or "",
        personality=data.personality or "",
        movement_style=data.movement_style or "",
        voice_description=data.voice_description or "",
        continuity_rules=data.continuity_rules or "",
        reference_images=json.dumps(data.reference_images or [])
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char

@router.get("/{project_id}/locations")
def list_locations(project_id: str, db: Session = Depends(get_db)):
    return db.query(Location).filter(Location.project_id == project_id).all()

@router.post("/{project_id}/locations")
def create_location(project_id: str, data: LocationCreate, db: Session = Depends(get_db)):
    loc = Location(
        project_id=project_id,
        name=data.name,
        description=data.description or "",
        architecture=data.architecture or "",
        interior_exterior=data.interior_exterior or "Interior",
        lighting=data.lighting or "",
        time_of_day=data.time_of_day or "Day",
        weather=data.weather or "Clear",
        color_mood=data.color_mood or "",
        important_objects=data.important_objects or "",
        continuity_rules=data.continuity_rules or "",
        reference_images=json.dumps(data.reference_images or [])
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc
