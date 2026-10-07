import os
import gc
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from backend.config import settings
from backend.services.video.base import VideoModel
from backend.logging_config import generation_logger

try:
    import torch
except ImportError:
    torch = None

class CogVideoX2BModel(VideoModel):
    """CogVideoX-2B Text-to-Video generation model optimized for T4 (16GB VRAM)."""

    def __init__(self, model_path_or_id: str = "THUDM/CogVideoX-2b", device: str = "cuda", dtype: str = "float16"):
        super().__init__(model_path_or_id, device, dtype)
        self.default_model_id = model_path_or_id

    def load(self, low_vram: bool = False):
        if self.is_loaded and self.pipeline is not None:
            return

        generation_logger.info(f"Loading CogVideoX-2B ({self.model_id}) on device={self.device}, low_vram={low_vram}")
        if torch is None or not torch.cuda.is_available() and self.device == "cuda":
            generation_logger.warning("CUDA is not available. Model loading will require PyTorch with CUDA on Kaggle T4.")
            self.device = "cpu"

        torch_dtype = torch.float16 if self.dtype == "float16" and torch.cuda.is_available() else torch.float32

        from diffusers import CogVideoXPipeline

        # Reset peak memory stats
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()

        # Persistent cache directory to prevent re-downloading across runs
        cache_dir = Path(settings.MODEL_DIR) / "hf_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Load pipeline
        self.pipeline = CogVideoXPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch_dtype,
            cache_dir=str(cache_dir)
        )

        # Apply T4 performance optimizations
        if self.device == "cuda" and torch.cuda.is_available():
            # T4 (Turing SM 7.5) has fast FP16 tensor cores and memory-efficient SDPA
            if hasattr(torch.backends.cuda, "enable_mem_efficient_sdp"):
                torch.backends.cuda.enable_mem_efficient_sdp(True)
            if hasattr(torch.backends.cuda, "enable_math_sdp"):
                torch.backends.cuda.enable_math_sdp(True)

            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            # CogVideoX-2B is only ~4.9GB in FP16 and fits completely in T4 16GB VRAM!
            # Direct VRAM residence eliminates slow PCIe layer swapping, boosting speed 4x-5x!
            if low_vram and total_vram_gb < 10.0:
                generation_logger.info("Enabling model CPU offload for CogVideoX-2B (VRAM < 10GB)")
                self.pipeline.enable_model_cpu_offload()
            else:
                generation_logger.info(f"Moving CogVideoX-2B directly to GPU VRAM for maximum speed (total VRAM={total_vram_gb:.1f}GB)")
                self.pipeline.to("cuda")

            # Disable diffusers safety checkers / black-frame filters if present
            if hasattr(self.pipeline, "safety_checker"):
                self.pipeline.safety_checker = None
            if hasattr(self.pipeline, "requires_safety_checker"):
                self.pipeline.requires_safety_checker = False

            # VAE Tiling and Slicing to prevent memory spikes during decode
            if hasattr(self.pipeline, "vae") and self.pipeline.vae is not None:
                if hasattr(self.pipeline.vae, "enable_tiling"):
                    self.pipeline.vae.enable_tiling()
                if hasattr(self.pipeline.vae, "enable_slicing"):
                    self.pipeline.vae.enable_slicing()

        self.is_loaded = True
        generation_logger.info("CogVideoX-2B loaded successfully.")

    def load_lora(self, lora_path: str, weight_name: Optional[str] = None, adapter_name: Optional[str] = None):
        """Loads custom LoRA weights into CogVideoX-2B."""
        if not self.is_loaded or self.pipeline is None:
            self.load()
        if hasattr(self.pipeline, "load_lora_weights"):
            generation_logger.info(f"Loading LoRA weights into CogVideoX-2B from {lora_path}")
            self.pipeline.load_lora_weights(lora_path, weight_name=weight_name, adapter_name=adapter_name)

    def unload(self):
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
        self.is_loaded = False
        gc.collect()
        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        generation_logger.info("CogVideoX-2B unloaded and VRAM cleared.")

    def generate(
        self,
        prompt: str,
        output_path: str,
        image_path: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        lora_path: Optional[str] = None,
        num_frames: int = 49,
        num_inference_steps: int = 25,
        guidance_scale: float = 6.0,
        seed: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Dict[str, Any]:
        if not self.is_loaded or self.pipeline is None:
            self.load()

        if lora_path and os.path.exists(lora_path):
            self.load_lora(lora_path)

        from diffusers.utils import export_to_video

        generator = None
        if seed is not None and torch is not None:
            generator = torch.Generator(device="cpu").manual_seed(seed)

        start_time = time.time()
        if torch is not None and torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        def callback_fn(pipe, step_index, timestep, callback_kwargs):
            if progress_callback:
                progress_pct = (step_index + 1) / num_inference_steps * 100.0
                progress_callback(step_index + 1, num_inference_steps, progress_pct)
            return callback_kwargs

        generation_logger.info(f"Starting CogVideoX-2B generation: prompt='{prompt[:50]}...', steps={num_inference_steps}, frames={num_frames}")

        try:
            pipe_kwargs = {
                "prompt": prompt,
                "num_videos_per_prompt": 1,
                "num_inference_steps": num_inference_steps,
                "num_frames": num_frames,
                "guidance_scale": guidance_scale,
                "generator": generator,
                "callback_on_step_end": callback_fn
            }
            if negative_prompt:
                pipe_kwargs["negative_prompt"] = negative_prompt

            video_result = self.pipeline(**pipe_kwargs).frames[0]

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            export_to_video(video_result, output_path, fps=8)

            gen_time = round(time.time() - start_time, 2)
            peak_vram_mb = 0.0
            if torch is not None and torch.cuda.is_available():
                peak_vram_mb = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2)

            generation_logger.info(f"Generation completed in {gen_time}s, peak VRAM={peak_vram_mb}MB. Saved to {output_path}")

            return {
                "success": True,
                "output_path": output_path,
                "generation_time": gen_time,
                "peak_vram_mb": peak_vram_mb,
                "frames": num_frames,
                "steps": num_inference_steps,
                "seed": seed
            }

        except Exception as e:
            err_str = str(e)
            is_oom = "out of memory" in err_str.lower() or "cuda oom" in err_str.lower()
            generation_logger.error(f"Generation error (OOM={is_oom}): {err_str}")
            # Free VRAM
            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise

    def estimate_memory_mb(self, resolution: str, frames: int) -> float:
        # CogVideoX-2B with model offload typically needs ~9-11 GB on T4
        return 9500.0

    def validate_config(self, resolution: str, frames: int, steps: int) -> bool:
        return frames in [49, 81] and steps >= 10
