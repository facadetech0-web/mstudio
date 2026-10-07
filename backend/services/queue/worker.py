import threading
import queue
import time
import datetime
import traceback
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.models.db import Job, Clip
from backend.services.video.manager import model_manager
from backend.logging_config import worker_logger

class GenerationWorker:
    """
    Background queue worker executing video generation jobs sequentially to
    respect GPU memory constraints on NVIDIA T4.
    """

    def __init__(self):
        self.job_queue = queue.Queue()
        self.is_running = True
        self.current_job_id: Optional[str] = None
        self.cancelled_job_ids = set()
        self.subscribers: List[queue.Queue] = []
        self._subscribers_lock = threading.Lock()

        # Start background worker thread
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def add_subscriber(self, q: queue.Queue):
        with self._subscribers_lock:
            self.subscribers.append(q)

    def remove_subscriber(self, q: queue.Queue):
        with self._subscribers_lock:
            if q in self.subscribers:
                self.subscribers.remove(q)

    def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        msg = {"type": event_type, "data": data, "timestamp": datetime.datetime.utcnow().isoformat()}
        with self._subscribers_lock:
            for sub in list(self.subscribers):
                try:
                    sub.put_nowait(msg)
                except Exception:
                    pass

    def enqueue_job(self, job_id: str):
        worker_logger.info(f"Enqueueing job {job_id}")
        self.job_queue.put(job_id)
        self.broadcast_event("job_queued", {"job_id": job_id})

    def cancel_job(self, job_id: str) -> bool:
        worker_logger.info(f"Requesting cancellation for job {job_id}")
        self.cancelled_job_ids.add(job_id)
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job and job.status in ("Waiting", "Running"):
                job.status = "Cancelled"
                db.commit()
                self.broadcast_event("job_cancelled", {"job_id": job_id})
                return True
        finally:
            db.close()
        return False

    def _worker_loop(self):
        worker_logger.info("Generation worker background loop started.")
        while self.is_running:
            try:
                job_id = self.job_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if job_id in self.cancelled_job_ids:
                worker_logger.info(f"Skipping cancelled job {job_id}")
                self.job_queue.task_done()
                continue

            self.current_job_id = job_id
            self._execute_job(job_id)
            self.current_job_id = None
            self.job_queue.task_done()

    def _execute_job(self, job_id: str):
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                worker_logger.error(f"Job {job_id} not found in database.")
                return

            if job.status == "Cancelled":
                return

            job.status = "Running"
            job.started_at = datetime.datetime.utcnow()
            job.progress = 0.0
            db.commit()

            clip = db.query(Clip).filter(Clip.id == job.clip_id).first() if job.clip_id else None
            if clip:
                if job.mode == "preview":
                    clip.preview_status = "Generating"
                else:
                    clip.final_status = "Generating"
                db.commit()

            self.broadcast_event("job_started", {
                "job_id": job.id,
                "clip_id": job.clip_id,
                "model": job.model,
                "mode": job.mode
            })

            # Check prompt and negative prompt
            prompt = (clip.video_prompt or clip.description or "Cinematic movie clip") if clip else "Cinematic movie clip"
            ref_image = clip.reference_image if clip else None

            # Automatic reference frame extraction for Image-to-Video models
            if ("5b" in job.model.lower() or job.mode == "final") and (not ref_image or not os.path.exists(ref_image)):
                frame_dir = Path("outputs") / (job.project_id or "default") / "references"
                frame_dir.mkdir(parents=True, exist_ok=True)
                extracted_path = (frame_dir / f"ref_{clip.id[:8] if clip else job.id[:8]}.png").as_posix()

                # Strategy 1: Extract first frame from generated preview video
                if clip and clip.preview_file and os.path.exists(clip.preview_file):
                    import subprocess
                    try:
                        subprocess.run([
                            "ffmpeg", "-y", "-ss", "0.1", "-i", clip.preview_file, "-vframes", "1", extracted_path
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                        if os.path.exists(extracted_path):
                            ref_image = extracted_path
                            clip.reference_image = extracted_path
                            db.commit()
                            generation_logger.info(f"Extracted reference frame from preview video: {ref_image}")
                    except Exception as ex:
                        generation_logger.warning(f"Could not extract frame from preview video: {ex}")

                # Strategy 2: Check shot reference image
                if (not ref_image or not os.path.exists(ref_image)) and clip:
                    shot = db.query(Shot).filter(Shot.id == clip.shot_id).first()
                    if shot and shot.reference_image and os.path.exists(shot.reference_image):
                        ref_image = shot.reference_image

                # Strategy 3: Create initial frame fallback canvas if none exists
                if not ref_image or not os.path.exists(ref_image):
                    try:
                        from PIL import Image
                        canvas = Image.new("RGB", (720, 480), color=(20, 20, 26))
                        canvas.save(extracted_path)
                        ref_image = extracted_path
                        if clip:
                            clip.reference_image = extracted_path
                            db.commit()
                        generation_logger.info(f"Created initial reference frame canvas: {ref_image}")
                    except Exception as ex:
                        generation_logger.warning(f"Could not create fallback canvas: {ex}")

            neg_prompt = (job.negative_prompt if hasattr(job, "negative_prompt") and job.negative_prompt else None) or (clip.negative_prompt if clip and clip.negative_prompt else None)
            lora_path = (job.lora_path if hasattr(job, "lora_path") and job.lora_path else None) or (clip.lora_path if clip and clip.lora_path else None)

            # Setup progress callback
            def progress_cb(current_step: int, total_steps: int, progress_pct: float):
                if job_id in self.cancelled_job_ids:
                    raise InterruptedError("Job was cancelled by user.")
                try:
                    job.steps_completed = current_step
                    job.total_steps = total_steps
                    job.progress = round(progress_pct, 1)
                    db.commit()
                    self.broadcast_event("job_progress", {
                        "job_id": job.id,
                        "clip_id": job.clip_id,
                        "steps_completed": current_step,
                        "total_steps": total_steps,
                        "progress": round(progress_pct, 1)
                    })
                except Exception as ex:
                    pass

            # Output destination path
            output_filename = f"{job.id}_{job.mode}.mp4"
            output_dir = Path("outputs") / (job.project_id or "default")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = (output_dir / output_filename).as_posix()

            # Determine low_vram flag from job or settings
            is_low_vram = "low_vram" in job.resolution.lower() or "5b" in job.model.lower()

            # Execute generation via model manager
            model = model_manager.load_model(job.model, low_vram=is_low_vram)

            gen_result = model.generate(
                prompt=prompt,
                output_path=output_path,
                image_path=ref_image,
                negative_prompt=neg_prompt,
                lora_path=lora_path,
                num_frames=job.frames or 49,
                num_inference_steps=job.steps or 25,
                seed=job.seed,
                progress_callback=progress_cb
            )

            job.status = "Completed"
            job.progress = 100.0
            job.completed_at = datetime.datetime.utcnow()
            job.generation_time = gen_result.get("generation_time")
            job.peak_vram = gen_result.get("peak_vram_mb")
            job.output_path = output_path
            db.commit()

            if clip:
                if job.mode == "preview":
                    clip.preview_status = "Ready"
                    clip.preview_file = output_path
                else:
                    clip.final_status = "Ready"
                    clip.final_file = output_path
                db.commit()

            self.broadcast_event("job_completed", {
                "job_id": job.id,
                "clip_id": job.clip_id,
                "output_path": output_path,
                "generation_time": job.generation_time,
                "peak_vram": job.peak_vram
            })

        except InterruptedError:
            worker_logger.info(f"Job {job_id} cancelled during execution.")
            job.status = "Cancelled"
            job.error = "Cancelled by user"
            db.commit()
            if clip:
                if job.mode == "preview":
                    clip.preview_status = "Draft"
                else:
                    clip.final_status = "Draft"
                db.commit()
            self.broadcast_event("job_cancelled", {"job_id": job_id})

        except Exception as e:
            worker_logger.error(f"Job {job_id} execution error:\n{traceback.format_exc()}")
            err_msg = str(e)
            if "out of memory" in err_msg.lower() or "cuda oom" in err_msg.lower():
                err_msg = "GPU memory is insufficient for this configuration. [Retry in Low VRAM Mode]"

            job.status = "Failed"
            job.error = err_msg
            job.completed_at = datetime.datetime.utcnow()
            db.commit()

            if clip:
                if job.mode == "preview":
                    clip.preview_status = "Error"
                else:
                    clip.final_status = "Error"
                db.commit()

            self.broadcast_event("job_failed", {
                "job_id": job.id,
                "clip_id": job.clip_id,
                "error": err_msg
            })
        finally:
            db.close()

generation_worker = GenerationWorker()
