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

class CogVideoX5BI2VModel(VideoModel):
    """
    CogVideoX-5B-I2V Image-to-Video generation model for high quality final video rendering.
    Specifically configured to execute within 16GB VRAM on Kaggle T4 via sequential offloading.
    """

    def __init__(self, model_path_or_id: str = "THUDM/CogVideoX-5b-I2V", device: str = "cuda", dtype: str = "float16"):
        super().__init__(model_path_or_id, device, dtype)
        self.default_model_id = model_path_or_id

    def load(self, low_vram: bool = True):
        if self.is_loaded and self.pipeline is not None:
            return

        generation_logger.info(f"Loading CogVideoX-5B-I2V ({self.model_id}) on device={self.device}, low_vram={low_vram}")
        if torch is None or (not torch.cuda.is_available() and self.device == "cuda"):
            generation_logger.warning("CUDA is not available. CogVideoX-5B requires Kaggle T4 GPU.")
            self.device = "cpu"

        torch_dtype = torch.float16 if self.dtype == "float16" and torch.cuda.is_available() else torch.float32

        # Disable unstable HF Xet transfer protocol which causes 'Background writer channel closed'
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

        from diffusers import CogVideoXImageToVideoPipeline

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()

        # Persistent cache directory to prevent re-downloading across runs
        cache_dir = Path(settings.MODEL_DIR) / "hf_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Clean up any corrupt or interrupted .incomplete files from previous failed downloads
        try:
            for incomplete_file in cache_dir.glob("**/*.incomplete"):
                if incomplete_file.is_file():
                    incomplete_file.unlink(missing_ok=True)
        except Exception:
            pass

        # Check available disk space
        import shutil
        try:
            free_gb = shutil.disk_usage(str(cache_dir)).free / (1024**3)
            generation_logger.info(f"Available disk space for CogVideoX-5B: {free_gb:.1f} GB")
            if free_gb < 12.0 and not Path(self.model_id).exists():
                generation_logger.warning(
                    f"⚠️ Low disk space ({free_gb:.1f}GB). Downloading 5B (~15GB) may exceed Kaggle 20GB disk limit. "
                    "Recommendation: Attach CogVideoX-5b-I2V as a Kaggle Dataset in /kaggle/input for 0-second 0-disk loading."
                )
        except Exception:
            pass

        # Load pipeline in fp16 with standard robust HTTP downloader
        self.pipeline = CogVideoXImageToVideoPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch_dtype,
            cache_dir=str(cache_dir)
        )

        # On T4 16GB, CogVideoX-5B must use sequential CPU offload or model offload with VAE tiling
        if self.device == "cuda" and torch.cuda.is_available():
            # Sequential CPU offload guarantees fitting 5B model into 16GB VRAM
            generation_logger.info("Enabling sequential CPU offloading for CogVideoX-5B-I2V")
            self.pipeline.enable_sequential_cpu_offload()

            # Disable diffusers safety checkers / black-frame filters if present
            if hasattr(self.pipeline, "safety_checker"):
                self.pipeline.safety_checker = None
            if hasattr(self.pipeline, "requires_safety_checker"):
                self.pipeline.requires_safety_checker = False

            if hasattr(self.pipeline, "vae") and self.pipeline.vae is not None:
                if hasattr(self.pipeline.vae, "enable_tiling"):
                    self.pipeline.vae.enable_tiling()
                if hasattr(self.pipeline.vae, "enable_slicing"):
                    self.pipeline.vae.enable_slicing()

        self.is_loaded = True
        generation_logger.info("CogVideoX-5B-I2V loaded successfully.")

    def load_lora(self, lora_path: str, weight_name: Optional[str] = None, adapter_name: Optional[str] = None):
        """Loads custom LoRA weights into CogVideoX-5B-I2V."""
        if not self.is_loaded or self.pipeline is None:
            self.load()
        if hasattr(self.pipeline, "load_lora_weights"):
            generation_logger.info(f"Loading LoRA weights into CogVideoX-5B-I2V from {lora_path}")
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
        generation_logger.info("CogVideoX-5B-I2V unloaded and VRAM cleared.")

    def generate(
        self,
        prompt: str,
        output_path: str,
        image_path: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        lora_path: Optional[str] = None,
        num_frames: int = 49,
        num_inference_steps: int = 30,
        guidance_scale: float = 6.0,
        seed: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Dict[str, Any]:
        if not self.is_loaded or self.pipeline is None:
            self.load()

        if lora_path and os.path.exists(lora_path):
            self.load_lora(lora_path)

        from diffusers.utils import export_to_video, load_image

        if not image_path or not os.path.exists(image_path):
            raise ValueError(
                f"CogVideoX-5B-I2V requires a reference image for final generation, but image_path '{image_path}' was not found."
            )

        # Load and resize reference image
        image = load_image(image_path)

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

        generation_logger.info(
            f"Starting CogVideoX-5B-I2V final generation: prompt='{prompt[:50]}...', image='{image_path}', steps={num_inference_steps}"
        )

        try:
            pipe_kwargs = {
                "prompt": prompt,
                "image": image,
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

            generation_logger.info(f"Final generation completed in {gen_time}s, peak VRAM={peak_vram_mb}MB. Saved to {output_path}")

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
            if is_oom:
                generation_logger.error(f"CogVideoX-5B-I2V could not fit into available GPU memory on T4: {err_str}")
            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()
            raise

    def estimate_memory_mb(self, resolution: str, frames: int) -> float:
        # CogVideoX-5B with sequential offload uses ~12-14 GB VRAM on T4
        return 13500.0

    def validate_config(self, resolution: str, frames: int, steps: int) -> bool:
        return frames in [49, 81] and steps >= 10
