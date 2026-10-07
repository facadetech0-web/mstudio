from typing import List, Optional
from pydantic import BaseModel, Field

class CharacterBibleItem(BaseModel):
    name: str
    age: str = ""
    gender: str = ""
    physical_description: str = ""
    face_description: str = ""
    hair: str = ""
    clothing: str = ""
    body_type: str = ""
    personality: str = ""
    movement_style: str = ""
    voice_description: str = ""
    continuity_rules: str = ""

class LocationBibleItem(BaseModel):
    name: str
    description: str = ""
    architecture: str = ""
    interior_exterior: str = "Interior"
    lighting: str = ""
    time: str = "Day"
    weather: str = "Clear"
    color_mood: str = ""
    important_objects: str = ""
    continuity_rules: str = ""

class MovieBible(BaseModel):
    title: str
    genre: str = "Cinematic"
    story: str = ""
    synopsis: str = ""
    visual_style: str = "Photorealistic film, 35mm anamorphic lens"
    color_palette: str = "Muted cinematic tones, natural contrast"
    mood: str = "Dramatic, immersive"
    camera_style: str = "Smooth steadycam, intentional composition"
    lighting_style: str = "High cinematic contrast, natural key light"
    time_period: str = "Contemporary"
    weather: str = "Atmospheric haze"
    characters: List[CharacterBibleItem] = Field(default_factory=list)
    locations: List[LocationBibleItem] = Field(default_factory=list)
    props: List[str] = Field(default_factory=list)
    continuity_rules: List[str] = Field(default_factory=list)
    negative_rules: List[str] = Field(default_factory=list)

class ScenePlanItem(BaseModel):
    scene_number: int
    title: str
    description: str
    location_name: str = ""
    characters: List[str] = Field(default_factory=list)
    time_of_day: str = "Day"
    weather: str = "Clear"
    visual_style: str = ""

class ScenesPlanResponse(BaseModel):
    project_title: str
    genre: str
    visual_style: str
    scenes: List[ScenePlanItem]

class ClipContinuityItem(BaseModel):
    clip_number: int
    description: str
    image_prompt: str
    video_prompt: str
    camera_motion: str = "Subtle slow forward tracking"
    subject_motion: str = "Realistic natural movement"
    duration_seconds: float = 5.0
    continuity_from_previous: Optional[str] = None
    continuity_to_next: Optional[str] = None

class ClipContinuityPlan(BaseModel):
    clip_count: int
    clips: List[ClipContinuityItem]

class PromptEnhanceResult(BaseModel):
    enhanced_image_prompt: str
    enhanced_video_prompt: str
    camera_motion: str
    subject_motion: str
    continuity_notes: str

class ContinuityCheckResult(BaseModel):
    is_consistent: bool
    character_checks: List[str] = Field(default_factory=list)
    location_checks: List[str] = Field(default_factory=list)
    temporal_checks: List[str] = Field(default_factory=list)
    story_checks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    auto_fix_plan: Optional[str] = None
