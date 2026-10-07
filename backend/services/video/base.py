from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from pathlib import Path

class VideoModel(ABC):
    """Abstract base class for video generation models (CogVideoX, Wan, LTX, etc.)."""

    def __init__(self, model_id: str, device: str = "cuda", dtype: str = "float16"):
        self.model_id = model_id
        self.device = device
        self.dtype = dtype
        self.is_loaded = False
        self.pipeline = None

    @abstractmethod
    def load(self, low_vram: bool = False):
        """Loads model into memory with memory optimizations."""
        pass

    @abstractmethod
    def unload(self):
        """Unloads model and releases VRAM."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        output_path: str,
        image_path: Optional[str] = None,
        num_frames: int = 49,
        num_inference_steps: int = 25,
        guidance_scale: float = 6.0,
        seed: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes video generation.
        Returns dict with status, execution metrics (generation_time, peak_vram, etc.).
        """
        pass

    @abstractmethod
    def estimate_memory_mb(self, resolution: str, frames: int) -> float:
        """Estimates VRAM in MB required for generation."""
        pass

    @abstractmethod
    def validate_config(self, resolution: str, frames: int, steps: int) -> bool:
        """Validates if configuration is valid for model and hardware."""
        pass
