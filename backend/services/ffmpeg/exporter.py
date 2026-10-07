import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.logging_config import api_logger

class FFmpegExporter:
    """Handles movie assembly, normalization, and export via FFmpeg."""

    def __init__(self):
        self.ffmpeg_cmd = self._find_ffmpeg()

    def _find_ffmpeg(self) -> Optional[str]:
        # Check system PATH
        cmd = shutil.which("ffmpeg")
        if cmd:
            return cmd

        # Check common Windows or imageio-ffmpeg paths
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
        except ImportError:
            pass

        return None

    def is_available(self) -> bool:
        return self.ffmpeg_cmd is not None

    def export_movie(
        self,
        clip_paths: List[str],
        output_path: str,
        resolution: str = "720p",
        fps: int = 24
    ) -> Dict[str, Any]:
        """
        Takes a list of approved clip video paths, normalizes them, and concatenates
        into a seamless MP4 movie.
        """
        if not self.is_available():
            raise RuntimeError(
                "FFmpeg is not installed or not found on system PATH. "
                "On Kaggle: run 'apt-get install -y ffmpeg'. On Windows: install FFmpeg or install imageio-ffmpeg."
            )

        if not clip_paths:
            raise ValueError("No clip paths provided for export.")

        for cp in clip_paths:
            if not os.path.exists(cp):
                raise FileNotFoundError(f"Video clip file not found: {cp}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        res_map = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "480p": (720, 480)
        }
        width, height = res_map.get(resolution, (1280, 720))

        # Use temporary directory to normalize each clip to identical resolution, fps, pixel format, and silent audio
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            normalized_clips = []

            for i, clip_file in enumerate(clip_paths):
                norm_file = str(temp_path / f"norm_{i:04d}.mp4")
                # Filter to scale and pad preserving aspect ratio, force fps and yuv420p
                vf_filter = (
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
                )

                # Command generates a silent audio track along with video
                cmd = [
                    self.ffmpeg_cmd,
                    "-y",
                    "-i", clip_file,
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-vf", vf_filter,
                    "-r", str(fps),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-shortest",
                    norm_file
                ]

                api_logger.info(f"Normalizing clip {i+1}/{len(clip_paths)}: {clip_file}")
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode != 0:
                    api_logger.error(f"FFmpeg normalization failed for {clip_file}: {res.stderr}")
                    raise RuntimeError(f"FFmpeg clip normalization error: {res.stderr[-500:]}")

                normalized_clips.append(norm_file)

            # Build concat list file
            concat_list_file = temp_path / "concat_list.txt"
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for n_file in normalized_clips:
                    safe_path = n_file.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")

            # Final concat pass
            concat_cmd = [
                self.ffmpeg_cmd,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_file),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_path
            ]

            api_logger.info(f"Concatenating {len(normalized_clips)} clips to {output_path}")
            concat_res = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if concat_res.returncode != 0:
                api_logger.error(f"FFmpeg concat failed: {concat_res.stderr}")
                raise RuntimeError(f"FFmpeg concatenation error: {concat_res.stderr[-500:]}")

        file_size_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        return {
            "success": True,
            "output_path": output_path,
            "clips_count": len(clip_paths),
            "resolution": f"{width}x{height}",
            "fps": fps,
            "file_size_bytes": file_size_bytes
        }

ffmpeg_exporter = FFmpegExporter()
