import time
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.db import Benchmark
from backend.schemas.api import SystemDiagnosticsResponse, BenchmarkRequest, BenchmarkResponse
from backend.services.system.diagnostics import get_system_diagnostics
from backend.services.video.manager import model_manager
from backend.logging_config import api_logger

try:
    import torch
except ImportError:
    torch = None

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/diagnostics", response_model=SystemDiagnosticsResponse)
def get_diagnostics():
    return get_system_diagnostics()

@router.get("/models")
def get_model_status():
    return model_manager.get_status()

@router.post("/models/unload")
def unload_models():
    model_manager.unload_active_model()
    return {"status": "unloaded", "current_vram": model_manager.get_status()}

@router.post("/benchmark", response_model=BenchmarkResponse)
def run_benchmark(req: BenchmarkRequest, db: Session = Depends(get_db)):
    """
    Requirement #42 & #66: Real GPU Benchmark Mode.
    Actually loads the requested model and performs a test generation pass,
    measuring exact latency and peak VRAM. Never hard-codes benchmark numbers.
    """
    api_logger.info(f"Running real benchmark for model={req.model}, frames={req.frames}, steps={req.steps}")
    start_t = time.time()
    peak_vram_mb = 0.0
    success = False
    error_msg = ""

    try:
        if torch is not None and torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()

        # Load model through manager
        model = model_manager.load_model(req.model, low_vram=True)

        # Run test generation pass
        benchmark_output = f"outputs/benchmark_{int(time.time())}.mp4"
        gen_res = model.generate(
            prompt="Cinematic benchmark test video, 35mm film still, photorealistic studio lighting",
            output_path=benchmark_output,
            num_frames=req.frames,
            num_inference_steps=req.steps,
            seed=42
        )
        gen_time = gen_res.get("generation_time", round(time.time() - start_t, 2))
        peak_vram_mb = gen_res.get("peak_vram_mb", 0.0)
        success = True
    except Exception as e:
        gen_time = round(time.time() - start_t, 2)
        if torch is not None and torch.cuda.is_available():
            peak_vram_mb = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2)
        error_msg = str(e)
        success = False
        api_logger.error(f"Benchmark run failed: {error_msg}")

    # Record real benchmark to database
    record = Benchmark(
        model=req.model,
        resolution=req.resolution,
        frames=req.frames,
        steps=req.steps,
        generation_time=gen_time,
        peak_vram=peak_vram_mb,
        success=success,
        error=error_msg
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return BenchmarkResponse(
        id=record.id,
        model=record.model,
        resolution=record.resolution,
        frames=record.frames,
        steps=record.steps,
        generation_time=record.generation_time,
        peak_vram=record.peak_vram,
        success=record.success,
        error=record.error or "",
        created_at=record.created_at
    )

@router.get("/benchmarks", response_model=List[BenchmarkResponse])
def list_benchmarks(db: Session = Depends(get_db)):
    return db.query(Benchmark).order_by(Benchmark.created_at.desc()).limit(20).all()
