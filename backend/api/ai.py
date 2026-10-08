from fastapi import APIRouter
from backend.schemas.api import (
    PlanMovieRequest,
    BreakIntoClipsRequest,
    EnhancePromptRequest,
    CheckContinuityRequest
)
from backend.services.ai.director import AIDirector

router = APIRouter(prefix="/api/ai", tags=["ai"])
ai_director = AIDirector()

@router.get("/status")
def check_ai_status():
    """Checks whether OpenRouter AI prompt connection is operational."""
    return ai_director.provider.test_connection()

@router.post("/plan-movie")
def plan_movie(req: PlanMovieRequest):
    bible = ai_director.generate_movie_bible(req.idea, req.genre or "Cinematic", req.visual_style or "")
    scenes = ai_director.break_into_scenes(bible, num_scenes=req.num_scenes or 3)
    return {
        "movie_bible": bible.model_dump(),
        "scenes": scenes.model_dump()
    }

@router.post("/break-into-clips")
def break_into_clips(req: BreakIntoClipsRequest):
    plan = ai_director.break_into_clips(
        scene_description=req.prompt,
        clip_count=req.clip_count,
        duration_per_clip=req.duration_per_clip,
        movie_bible_context=req.current_scene_context
    )
    return plan.model_dump()

@router.post("/enhance-prompt")
def enhance_prompt(req: EnhancePromptRequest):
    result = ai_director.enhance_prompt(
        raw_prompt=req.prompt,
        prompt_type=req.prompt_type,
        scene_context=req.scene_context
    )
    return result.model_dump()

@router.post("/check-continuity")
def check_continuity(req: CheckContinuityRequest):
    result = ai_director.check_continuity(req.clips_data or [])
    return result.model_dump()
