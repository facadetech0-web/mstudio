import sys
import os
import shutil
from pathlib import Path
from typing import Dict, Any

from backend.config import settings
from backend.services.ffmpeg.exporter import ffmpeg_exporter

def get_system_diagnostics() -> Dict[str, Any]:
    # PyTorch & CUDA
    pytorch_version = "Not installed"
    cuda_available = False
    gpu_name = None
    gpu_total_vram_gb = None
    gpu_free_vram_gb = None

    try:
        import torch
        pytorch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            free_b, total_b = torch.cuda.mem_get_info()
            gpu_total_vram_gb = round(total_b / (1024**3), 2)
            gpu_free_vram_gb = round(free_b / (1024**3), 2)
    except ImportError:
        pass

    # OpenRouter
    openrouter_configured = bool(settings.OPENROUTER_API_KEY and len(settings.OPENROUTER_API_KEY.strip()) > 5)

    # Models presence
    model_dir = Path(settings.MODEL_DIR)
    models_status = {
        "cogvideox-2b": (model_dir / "cogvideox-2b").exists() or bool(os.getenv("HF_HOME") or os.path.expanduser("~/.cache/huggingface")),
        "cogvideox-5b-i2v": (model_dir / "cogvideox-5b-i2v").exists() or bool(os.getenv("HF_HOME") or os.path.expanduser("~/.cache/huggingface"))
    }

    t4_recommended_settings = {
        "target_hardware": "NVIDIA T4 16GB VRAM (Kaggle)",
        "precision": "fp16",
        "cpu_offload": True,
        "vae_tiling": True,
        "vae_slicing": True,
        "preview_steps": 20,
        "preview_frames": 49,
        "final_steps": 25,
        "final_frames": 49
    }

    return {
        "python_version": sys.version.split()[0],
        "pytorch_version": pytorch_version,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "gpu_total_vram_gb": gpu_total_vram_gb,
        "gpu_free_vram_gb": gpu_free_vram_gb,
        "ffmpeg_available": ffmpeg_exporter.is_available(),
        "sqlite_available": True,
        "openrouter_configured": openrouter_configured,
        "openrouter_model": settings.OPENROUTER_MODEL,
        "models_status": models_status,
        "t4_recommended_settings": t4_recommended_settings
    }
