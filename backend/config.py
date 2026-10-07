import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODEL_DIR: str = os.getenv("MODEL_DIR", "./models")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./outputs")
    PROJECTS_DIR: str = os.getenv("PROJECTS_DIR", "./projects")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "./logs")

    PREVIEW_MODEL: str = os.getenv("PREVIEW_MODEL", "cogvideox-2b")
    FINAL_MODEL: str = os.getenv("FINAL_MODEL", "cogvideox-5b-i2v")

    DEVICE: str = os.getenv("DEVICE", "cuda")
    DTYPE: str = os.getenv("DTYPE", "float16")

    ENABLE_CPU_OFFLOAD: bool = os.getenv("ENABLE_CPU_OFFLOAD", "true").lower() in ("true", "1", "yes")
    ENABLE_VAE_TILING: bool = os.getenv("ENABLE_VAE_TILING", "true").lower() in ("true", "1", "yes")
    ENABLE_VAE_SLICING: bool = os.getenv("ENABLE_VAE_SLICING", "true").lower() in ("true", "1", "yes")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./movie_studio.db")

    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "qwen/qwen3.5-flash-02-23")
    OPENROUTER_TEMPERATURE: float = float(os.getenv("OPENROUTER_TEMPERATURE", "0.7"))
    OPENROUTER_MAX_TOKENS: int = int(os.getenv("OPENROUTER_MAX_TOKENS", "4000"))

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure base directories exist
for folder in [settings.MODEL_DIR, settings.OUTPUT_DIR, settings.PROJECTS_DIR, settings.LOGS_DIR]:
    Path(folder).mkdir(parents=True, exist_ok=True)
