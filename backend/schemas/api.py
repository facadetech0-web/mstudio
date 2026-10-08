from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime
from backend.schemas.ai import MovieBible

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    genre: Optional[str] = "Cinematic"
    visual_style: Optional[str] = "Photorealistic 35mm film"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    visual_style: Optional[str] = None
    movie_bible: Optional[Dict[str, Any]] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    genre: str
    visual_style: str
    movie_bible: Dict[str, Any]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class CharacterCreate(BaseModel):
    name: str
    age: Optional[str] = ""
    gender: Optional[str] = ""
    physical_description: Optional[str] = ""
    face_description: Optional[str] = ""
    hair: Optional[str] = ""
    clothing: Optional[str] = ""
    body_type: Optional[str] = ""
    personality: Optional[str] = ""
    movement_style: Optional[str] = ""
    voice_description: Optional[str] = ""
    continuity_rules: Optional[str] = ""
    reference_images: Optional[List[str]] = Field(default_factory=list)

class CharacterResponse(CharacterCreate):
    id: str
    project_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    architecture: Optional[str] = ""
    interior_exterior: Optional[str] = "Interior"
    lighting: Optional[str] = ""
    time_of_day: Optional[str] = "Day"
    weather: Optional[str] = "Clear"
    color_mood: Optional[str] = ""
    important_objects: Optional[str] = ""
    continuity_rules: Optional[str] = ""
    reference_images: Optional[List[str]] = Field(default_factory=list)

class LocationResponse(LocationCreate):
    id: str
    project_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class SceneCreate(BaseModel):
    scene_number: int = 1
    title: str
    description: Optional[str] = ""
    location_id: Optional[str] = None
    location_name: Optional[str] = ""
    characters: Optional[List[str]] = Field(default_factory=list)
    time_of_day: Optional[str] = "Day"
    weather: Optional[str] = "Clear"
    visual_style: Optional[str] = ""

class SceneResponse(SceneCreate):
    id: str
    project_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class ShotCreate(BaseModel):
    shot_number: int = 1
    description: Optional[str] = ""
    reference_image: Optional[str] = ""
    image_prompt: Optional[str] = ""
    video_prompt: Optional[str] = ""
    camera_motion: Optional[str] = "Slow smooth camera move"
    subject_motion: Optional[str] = "Subtle cinematic movement"
    duration: float = 5.0
    clip_count: int = 1

class ShotResponse(ShotCreate):
    id: str
    scene_id: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class ClipCreate(BaseModel):
    clip_number: int = 1
    description: Optional[str] = ""
    reference_image: Optional[str] = ""
    image_prompt: Optional[str] = ""
    video_prompt: Optional[str] = ""
    negative_prompt: Optional[str] = ""
    lora_path: Optional[str] = ""
    camera_motion: Optional[str] = ""
    subject_motion: Optional[str] = ""
    duration: float = 5.0
    continuity_from_previous: Optional[str] = None
    continuity_to_next: Optional[str] = None
    timeline_order: Optional[int] = 1

class ClipUpdate(BaseModel):
    description: Optional[str] = None
    reference_image: Optional[str] = None
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    lora_path: Optional[str] = None
    camera_motion: Optional[str] = None
    subject_motion: Optional[str] = None
    duration: Optional[float] = None
    timeline_order: Optional[int] = None
    preview_status: Optional[str] = None
    final_status: Optional[str] = None
    seed: Optional[int] = None

class ClipResponse(ClipCreate):
    id: str
    shot_id: str
    scene_id: str
    project_id: str
    timeline_order: int
    preview_status: str
    final_status: str
    preview_file: str
    final_file: str
    seed: Optional[int]
    prompt_history: List[Any]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class GenerateRequest(BaseModel):
    clip_ids: Optional[List[str]] = None
    mode: str = "preview" # preview or final
    resolution: Optional[str] = "720x480"
    steps: Optional[int] = 25
    frames: Optional[int] = 49
    seed: Optional[int] = None
    low_vram: Optional[bool] = False
    model: Optional[str] = None
    negative_prompt: Optional[str] = None
    lora_path: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    project_id: str
    scene_id: Optional[str]
    shot_id: Optional[str]
    clip_id: Optional[str]
    mode: str
    model: str
    status: str
    progress: float
    steps_completed: int
    total_steps: int
    seed: Optional[int]
    resolution: str
    frames: int
    steps: int
    created_at: datetime.datetime
    started_at: Optional[datetime.datetime]
    completed_at: Optional[datetime.datetime]
    generation_time: Optional[float]
    peak_vram: Optional[float]
    output_path: str
    error: str

    class Config:
        from_attributes = True

class ExportRequest(BaseModel):
    resolution: str = "720p" # 720p or 1080p
    fps: int = 24
    include_only_approved: bool = True

class BenchmarkRequest(BaseModel):
    model: str = "cogvideox-2b"
    resolution: str = "720x480"
    frames: int = 49
    steps: int = 15

class BenchmarkResponse(BaseModel):
    id: str
    model: str
    resolution: str
    frames: int
    steps: int
    generation_time: float
    peak_vram: float
    success: bool
    error: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PlanMovieRequest(BaseModel):
    idea: str
    genre: Optional[str] = "Cinematic"
    visual_style: Optional[str] = "Photorealistic film, 35mm lens"

class BreakIntoClipsRequest(BaseModel):
    prompt: str
    clip_count: int = Field(default=1, ge=1)
    duration_per_clip: float = Field(default=5.0, ge=1.0)
    current_scene_context: Optional[str] = ""

class EnhancePromptRequest(BaseModel):
    prompt: str
    prompt_type: str = "both" # "image", "video", or "both"
    scene_context: Optional[str] = ""

class CheckContinuityRequest(BaseModel):
    scene_id: Optional[str] = None
    clips_data: Optional[List[Dict[str, Any]]] = None

class SystemDiagnosticsResponse(BaseModel):
    python_version: str
    pytorch_version: str
    cuda_available: bool
    gpu_name: Optional[str]
    gpu_total_vram_gb: Optional[float]
    gpu_free_vram_gb: Optional[float]
    ffmpeg_available: bool
    sqlite_available: bool
    openrouter_configured: bool
    openrouter_model: str
    models_status: Dict[str, bool]
    t4_recommended_settings: Dict[str, Any]
