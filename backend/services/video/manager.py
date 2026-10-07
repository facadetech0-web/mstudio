import os
import gc
from typing import Dict, Any, Optional
from pathlib import Path

from backend.config import settings
from backend.logging_config import generation_logger
from backend.services.video.base import VideoModel
from backend.services.video.cogvideox2b import CogVideoX2BModel
from backend.services.video.cogvideox5b_i2v import CogVideoX5BI2VModel

try:
    import torch
except ImportError:
    torch = None

class ModelManager:
    """
    Manages video generation model lifecycles, VRAM allocation, and single-model residency.
    """

    def __init__(self):
        self.models: Dict[str, VideoModel] = {}
        self.active_model_name: Optional[str] = None
        self._register_default_models()

    def _register_default_models(self):
        # Check if local weights exist in MODEL_DIR or use Hugging Face repos
        model_dir = Path(settings.MODEL_DIR)
        cog2b_path = str(model_dir / "cogvideox-2b") if (model_dir / "cogvideox-2b").exists() else "THUDM/CogVideoX-2b"
        cog5b_path = str(model_dir / "cogvideox-5b-i2v") if (model_dir / "cogvideox-5b-i2v").exists() else "THUDM/CogVideoX-5b-I2V"

        self.models["cogvideox-2b"] = CogVideoX2BModel(
            model_path_or_id=cog2b_path,
            device=settings.DEVICE,
            dtype=settings.DTYPE
        )
        self.models["cogvideox-5b-i2v"] = CogVideoX5BI2VModel(
            model_path_or_id=cog5b_path,
            device=settings.DEVICE,
            dtype=settings.DTYPE
        )

    def _normalize_name(self, name: str) -> str:
        if not name:
            return "cogvideox-2b"
        key = name.lower().strip()
        if "5b" in key:
            return "cogvideox-5b-i2v"
        if "2b" in key:
            return "cogvideox-2b"
        return key

    def register_model(self, name: str, model_instance: VideoModel):
        """Allows registering future models like Wan 2.1 or LTX Video."""
        self.models[self._normalize_name(name)] = model_instance

    def get_model(self, model_name: str) -> VideoModel:
        key = self._normalize_name(model_name)
        if key not in self.models:
            raise ValueError(f"Model '{model_name}' is not registered. Available models: {list(self.models.keys())}")
        return self.models[key]

    def load_model(self, model_name: str, low_vram: bool = False) -> VideoModel:
        key = self._normalize_name(model_name)
        if key not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        # If another heavy model is loaded, unload it first to prevent VRAM overflow
        if self.active_model_name and self.active_model_name != key:
            generation_logger.info(f"Unloading current active model '{self.active_model_name}' before loading '{key}'")
            self.unload_active_model()

        model = self.models[key]
        if not model.is_loaded:
            model.load(low_vram=low_vram)
            self.active_model_name = key

        return model

    def unload_active_model(self):
        if self.active_model_name and self.active_model_name in self.models:
            self.models[self.active_model_name].unload()
            self.active_model_name = None

        gc.collect()
        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_status(self) -> Dict[str, Any]:
        allocated_vram = 0.0
        free_vram = 0.0
        total_vram = 0.0

        if torch is not None and torch.cuda.is_available():
            allocated_vram = round(torch.cuda.memory_allocated() / (1024 * 1024 * 1024), 2)
            free_b, total_b = torch.cuda.mem_get_info()
            free_vram = round(free_b / (1024 * 1024 * 1024), 2)
            total_vram = round(total_b / (1024 * 1024 * 1024), 2)

        return {
            "active_model": self.active_model_name,
            "models_available": list(self.models.keys()),
            "models_loaded": {name: model.is_loaded for name, model in self.models.items()},
            "cuda_available": torch is not None and torch.cuda.is_available(),
            "allocated_vram_gb": allocated_vram,
            "free_vram_gb": free_vram,
            "total_vram_gb": total_vram
        }

model_manager = ModelManager()
