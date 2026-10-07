import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    genre = Column(String(100), default="Cinematic")
    visual_style = Column(String(255), default="Photorealistic film, 35mm lens")
    movie_bible = Column(Text, default="{}")  # Stored as JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_number")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")

class Character(Base):
    __tablename__ = "characters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(String(50), default="")
    gender = Column(String(50), default="")
    physical_description = Column(Text, default="")
    face_description = Column(Text, default="")
    hair = Column(String(255), default="")
    clothing = Column(Text, default="")
    body_type = Column(String(100), default="")
    personality = Column(Text, default="")
    movement_style = Column(String(255), default="")
    voice_description = Column(String(255), default="")
    reference_images = Column(Text, default="[]")  # JSON list of paths
    continuity_rules = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="characters")

class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    architecture = Column(String(255), default="")
    interior_exterior = Column(String(50), default="Interior")
    lighting = Column(String(255), default="")
    time_of_day = Column(String(100), default="Day")
    weather = Column(String(100), default="Clear")
    color_mood = Column(String(255), default="")
    important_objects = Column(Text, default="")
    reference_images = Column(Text, default="[]")  # JSON list of paths
    continuity_rules = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="locations")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_number = Column(Integer, default=1)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    location_id = Column(String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    location_name = Column(String(255), default="")
    characters_json = Column(Text, default="[]")  # JSON list of character names or IDs
    time_of_day = Column(String(100), default="Day")
    weather = Column(String(100), default="Clear")
    visual_style = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="scenes")
    shots = relationship("Shot", back_populates="scene", cascade="all, delete-orphan", order_by="Shot.shot_number")

class Shot(Base):
    __tablename__ = "shots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    shot_number = Column(Integer, default=1)
    description = Column(Text, default="")
    reference_image = Column(String(500), default="")
    image_prompt = Column(Text, default="")
    video_prompt = Column(Text, default="")
    camera_motion = Column(String(255), default="Static / Slight pan")
    subject_motion = Column(String(255), default="Natural subtle movement")
    duration = Column(Float, default=5.0)
    clip_count = Column(Integer, default=1)
    status = Column(String(50), default="Draft")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    scene = relationship("Scene", back_populates="shots")
    clips = relationship("Clip", back_populates="shot", cascade="all, delete-orphan", order_by="Clip.clip_number")

class Clip(Base):
    __tablename__ = "clips"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    shot_id = Column(String(36), ForeignKey("shots.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), nullable=False)
    project_id = Column(String(36), nullable=False)
    clip_number = Column(Integer, default=1)
    timeline_order = Column(Integer, default=1)
    description = Column(Text, default="")
    reference_image = Column(String(500), default="")
    image_prompt = Column(Text, default="")
    video_prompt = Column(Text, default="")
    negative_prompt = Column(Text, default="")
    lora_path = Column(String(500), default="")
    camera_motion = Column(String(255), default="")
    subject_motion = Column(String(255), default="")
    duration = Column(Float, default=5.0)
    continuity_from_previous = Column(Text, nullable=True)
    continuity_to_next = Column(Text, nullable=True)
    preview_status = Column(String(50), default="Draft") # Draft, Queued, Generating, Ready, Approved, Rejected, Error
    final_status = Column(String(50), default="Draft")   # Draft, Queued, Generating, Ready, Error
    preview_file = Column(String(500), default="")
    final_file = Column(String(500), default="")
    seed = Column(Integer, nullable=True)
    prompt_history = Column(Text, default="[]")  # JSON list of prompt versions
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    shot = relationship("Shot", back_populates="clips")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String(50), default="reference_image") # character_ref, location_ref, frame_ref, video_preview, video_final
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(100), default="image/png")
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="assets")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), nullable=True)
    shot_id = Column(String(36), nullable=True)
    clip_id = Column(String(36), nullable=True)
    mode = Column(String(50), default="preview") # preview, final, benchmark
    model = Column(String(100), default="cogvideox-2b")
    status = Column(String(50), default="Waiting") # Waiting, Running, Completed, Failed, Cancelled
    progress = Column(Float, default=0.0) # 0 to 100
    steps_completed = Column(Integer, default=0)
    total_steps = Column(Integer, default=25)
    seed = Column(Integer, nullable=True)
    resolution = Column(String(50), default="720x480")
    frames = Column(Integer, default=49)
    steps = Column(Integer, default=25)
    negative_prompt = Column(Text, default="")
    lora_path = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    generation_time = Column(Float, nullable=True)
    peak_vram = Column(Float, nullable=True) # in MB / GB
    output_path = Column(String(500), default="")
    error = Column(Text, default="")

    project = relationship("Project", back_populates="jobs")

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model = Column(String(100), nullable=False)
    resolution = Column(String(50), nullable=False)
    frames = Column(Integer, default=49)
    steps = Column(Integer, default=25)
    generation_time = Column(Float, default=0.0)
    peak_vram = Column(Float, default=0.0) # MB
    success = Column(Boolean, default=True)
    error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
