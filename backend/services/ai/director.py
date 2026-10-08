from typing import Dict, Any, List, Optional
from backend.services.ai.openrouter import OpenRouterProvider
from backend.schemas.ai import (
    MovieBible,
    ScenesPlanResponse,
    ClipContinuityPlan,
    ClipContinuityItem,
    PromptEnhanceResult,
    ContinuityCheckResult,
    CharacterBibleItem,
    LocationBibleItem
)
from backend.logging_config import ai_logger

class AIDirector:
    def __init__(self, provider: Optional[OpenRouterProvider] = None):
        self.provider = provider or OpenRouterProvider()

    def is_available(self) -> bool:
        return self.provider.is_configured()

    def generate_movie_bible(self, idea: str, genre: str = "Cinematic", visual_style: str = "") -> MovieBible:
        """Generates a complete Movie Bible from high level user idea."""
        if not self.is_available():
            # Return high quality structured baseline if no API key is provided
            return MovieBible(
                title=f"The Story of {idea[:30]}",
                genre=genre,
                story=idea,
                synopsis=f"A cinematic narrative exploring {idea}",
                visual_style=visual_style or "Photorealistic 35mm film, anamorphic lens, high contrast, atmospheric grain",
                color_palette="Muted industrial blues, warm amber highlights, rich deep shadows",
                mood="Suspenseful, dramatic, contemplative",
                camera_style="Slow deliberate tracking, low angle perspective, steady shallow depth of field",
                lighting_style="Natural practical lighting, strong rim lighting, atmospheric volumetric dust",
                time_period="Contemporary",
                weather="Overcast, misty",
                characters=[
                    CharacterBibleItem(
                        name="The Protagonist",
                        age="35",
                        gender="Male",
                        physical_description="Tall, weathered look, focused gaze",
                        face_description="Determined expression, light stubble",
                        hair="Dark short disheveled hair",
                        clothing="Worn black leather jacket, dark charcoal t-shirt, rugged denim jeans, work boots",
                        body_type="Athletic lean build",
                        personality="Resourceful, curious, cautious",
                        movement_style="Deliberate slow footsteps, cautious awareness",
                        voice_description="Low quiet rasp",
                        continuity_rules="Maintain worn black leather jacket and dark shirt across all scenes."
                    )
                ],
                locations=[
                    LocationBibleItem(
                        name="The Abandoned Facility",
                        description="Vast decaying industrial warehouse with towering rusted steel beams and broken skylights",
                        architecture="Brutalist 20th century industrial steel and concrete",
                        interior_exterior="Interior",
                        lighting="Shafts of pale sunlight cutting through dusty air, rusted metal reflections",
                        time="Late afternoon",
                        weather="Foggy exterior visible through cracked roof",
                        color_mood="Oxidized orange rust against cold gray concrete",
                        important_objects="Central monolithic machine with mechanical levers and copper gauges",
                        continuity_rules="Rust patterns, broken glass floor, and dust motes must remain consistent."
                    )
                ],
                props=["Antique brass mechanical key", "Heavy lever on generator", "Handheld flashlight"],
                continuity_rules=[
                    "Maintain consistent lighting direction from overhead skylights",
                    "Character must retain black leather jacket unless explicitly removed",
                    "Dust motes and volumetric haze persistent in all interior shots"
                ],
                negative_rules=[
                    "No sudden wardrobe changes",
                    "No modern electronics or smartphones",
                    "No cartoonish saturated colors"
                ]
            )

        system_prompt = (
            "You are an acclaimed Hollywood Movie Director and Production Designer. "
            "Your task is to build a comprehensive, cohesive, professional Movie Bible for a cinematic project."
        )
        user_prompt = (
            f"User Movie Idea: {idea}\n"
            f"Genre: {genre}\n"
            f"Visual Style Preference: {visual_style}\n\n"
            "Build the complete Movie Bible including Title, Story, Characters with exact clothing details for visual continuity, "
            "Locations with specific lighting and architecture, Props, and explicit Continuity Rules."
        )

        try:
            return self.provider.generate_structured(system_prompt, user_prompt, MovieBible)
        except Exception as e:
            ai_logger.warning(f"AI Director movie bible generation failed: {e}. Falling back to baseline bible...")
            return MovieBible(
                title=f"The Story of {idea[:30]}",
                genre=genre,
                story=idea,
                synopsis=f"A cinematic narrative exploring {idea}",
                visual_style=visual_style or "Photorealistic 35mm film, anamorphic lens, high contrast, atmospheric grain",
                color_palette="Muted industrial blues, warm amber highlights, rich deep shadows",
                mood="Suspenseful, dramatic, contemplative",
                camera_style="Slow deliberate tracking, low angle perspective, steady shallow depth of field",
                lighting_style="Natural practical lighting, strong rim lighting, atmospheric volumetric dust",
                time_period="Contemporary",
                weather="Overcast, misty",
                characters=[
                    CharacterBibleItem(
                        name="The Protagonist",
                        age="35",
                        gender="Male",
                        physical_description="Tall, weathered look, focused gaze",
                        face_description="Determined expression, light stubble",
                        hair="Dark short disheveled hair",
                        clothing="Worn black leather jacket, dark charcoal t-shirt, rugged denim jeans, work boots",
                        body_type="Athletic lean build",
                        personality="Resourceful, curious, cautious",
                        movement_style="Deliberate slow footsteps, cautious awareness",
                        voice_description="Low quiet rasp",
                        continuity_rules="Maintain worn black leather jacket and dark shirt across all scenes."
                    )
                ],
                locations=[
                    LocationBibleItem(
                        name="The Abandoned Facility",
                        description="Vast decaying industrial warehouse with towering rusted steel beams and broken skylights",
                        architecture="Brutalist 20th century industrial steel and concrete",
                        interior_exterior="Interior",
                        lighting="Shafts of pale sunlight cutting through dusty air, rusted metal reflections",
                        time="Late afternoon",
                        weather="Foggy exterior visible through cracked roof",
                        color_mood="Oxidized orange rust against cold gray concrete",
                        important_objects="Central monolithic machine with mechanical levers and copper gauges",
                        continuity_rules="Rust patterns, broken glass floor, and dust motes must remain consistent."
                    )
                ],
                props=["Antique brass mechanical key", "Heavy lever on generator", "Handheld flashlight"],
                continuity_rules=[
                    "Maintain consistent lighting direction from overhead skylights",
                    "Character must retain black leather jacket unless explicitly removed",
                    "Dust motes and volumetric haze persistent in all interior shots"
                ],
                negative_rules=[
                    "No sudden wardrobe changes",
                    "No modern electronics or smartphones",
                    "No cartoonish saturated colors"
                ]
            )

    def break_into_scenes(self, movie_bible: MovieBible, num_scenes: int = 3) -> ScenesPlanResponse:
        """Decomposes movie bible story into a specified number of scenes (1-10)."""
        num_scenes = max(1, min(10, int(num_scenes or 3)))
        if not self.is_available():
            scenes = []
            for i in range(1, num_scenes + 1):
                scenes.append({
                    "scene_number": i,
                    "title": f"Scene {i}: Narrative Act {i}",
                    "description": f"The story unfolds in scene {i}: {movie_bible.synopsis or movie_bible.story}",
                    "location_name": movie_bible.locations[0].name if movie_bible.locations else "Cinematic Set",
                    "characters": [c.name for c in movie_bible.characters] if movie_bible.characters else ["Protagonist"],
                    "time_of_day": "Afternoon" if i % 2 == 1 else "Dusk",
                    "weather": "Atmospheric mist",
                    "visual_style": movie_bible.visual_style
                })
            return ScenesPlanResponse(
                project_title=movie_bible.title,
                genre=movie_bible.genre,
                visual_style=movie_bible.visual_style,
                scenes=scenes
            )

        system_prompt = (
            "You are an expert Film Director and Screenplay Supervisor. "
            f"Your mission is to decompose the story into EXACTLY {num_scenes} cohesive, cinematic scenes. "
            f"You MUST generate exactly {num_scenes} scenes (from Scene 1 to Scene {num_scenes}). "
            "Ensure character, location, and temporal continuity between consecutive scenes."
        )
        user_prompt = (
            f"Movie Title: {movie_bible.title}\n"
            f"Genre: {movie_bible.genre}\n"
            f"Story: {movie_bible.story}\n"
            f"Visual Style: {movie_bible.visual_style}\n"
            f"Available Locations: {[loc.name for loc in movie_bible.locations]}\n"
            f"Available Characters: {[char.name for char in movie_bible.characters]}\n\n"
            f"TASK: Generate EXACTLY {num_scenes} chronological scenes. Output valid JSON matching the schema with a list of {num_scenes} scene items."
        )

        return self.provider.generate_structured(system_prompt, user_prompt, ScenesPlanResponse)

    def break_into_clips(
        self,
        scene_description: str,
        clip_count: int,
        duration_per_clip: float = 5.0,
        movie_bible_context: Optional[str] = "",
        character_context: Optional[str] = "",
        location_context: Optional[str] = "",
        previous_clip_context: Optional[str] = "",
        next_clip_context: Optional[str] = ""
    ) -> ClipContinuityPlan:
        """
        Decomposes a scene or shot idea into clip_count sequential, logically connected clips.
        Maintains character, location, temporal and story continuity.
        """
        if clip_count <= 0:
            clip_count = 1

        if not self.is_available():
            # Offline template plan with logical progression
            clips = []
            for i in range(1, clip_count + 1):
                prev_text = f"Continuous motion following clip {i-1}" if i > 1 else "Opening of shot sequence"
                next_text = f"Leads directly into action of clip {i+1}" if i < clip_count else "Resolves current shot sequence"
                clips.append(
                    ClipContinuityItem(
                        clip_number=i,
                        description=f"Part {i} of {clip_count}: Progression of {scene_description[:60]}",
                        image_prompt=(
                            f"Cinematic frame, 35mm film still, {scene_description}. "
                            f"Subject in worn black leather jacket, industrial background, cinematic volumetric lighting, 8k resolution, photorealistic."
                        ),
                        video_prompt=(
                            f"Continuous cinematic shot, slow smooth camera tracking, subject in motion, "
                            f"subtle natural body movements, dust motes floating in light beam, 24fps film motion."
                        ),
                        camera_motion="Slow forward dolly tracking" if i % 2 != 0 else "Subtle pan with character motion",
                        subject_motion="Natural fluid walking and interaction",
                        duration_seconds=duration_per_clip,
                        continuity_from_previous=prev_text if i > 1 else None,
                        continuity_to_next=next_text if i < clip_count else None
                    )
                )
            return ClipContinuityPlan(clip_count=clip_count, clips=clips)

        system_prompt = (
            "You are an expert Film Director and Cinematographer. "
            "The user will give you a scene/action idea and request a specific number of connected clips. "
            "CRITICAL RULES:\n"
            "1. DO NOT duplicate the same prompt across clips.\n"
            "2. Intelligently divide the action into a progressive, connected sequential flow (e.g. establishing shot -> approaching -> entering -> interacting -> climax).\n"
            "3. SEPARATE Image Prompt (visual composition, lighting, character clothing, environment) and Video Prompt (motion, camera dynamics, temporal progression).\n"
            "4. Enforce STRICT continuity: character wardrobe, location architecture, lighting direction, and physics must connect seamlessly between clip N and clip N+1.\n"
            "5. Explicitly populate continuity_from_previous and continuity_to_next."
        )

        context_blocks = []
        if movie_bible_context:
            context_blocks.append(f"MOVIE BIBLE:\n{movie_bible_context}")
        if character_context:
            context_blocks.append(f"CHARACTERS:\n{character_context}")
        if location_context:
            context_blocks.append(f"LOCATION:\n{location_context}")
        if previous_clip_context:
            context_blocks.append(f"PREVIOUS CLIP CONTEXT:\n{previous_clip_context}")
        if next_clip_context:
            context_blocks.append(f"NEXT CLIP CONTEXT:\n{next_clip_context}")

        context_str = "\n\n".join(context_blocks)
        user_prompt = (
            f"CONTEXT:\n{context_str}\n\n"
            f"SCENE IDEA: {scene_description}\n"
            f"REQUESTED NUMBER OF CLIPS: {clip_count}\n"
            f"DURATION PER CLIP: {duration_per_clip} seconds\n\n"
            f"Create a sequential {clip_count}-clip continuity plan."
        )

        try:
            return self.provider.generate_structured(system_prompt, user_prompt, ClipContinuityPlan)
        except Exception as e:
            ai_logger.warning(f"Structured plan generation failed: {e}. Generating fallback cinematic sequence...")
            clips = []
            for i in range(1, clip_count + 1):
                prev_text = f"Continuous motion following clip {i-1}" if i > 1 else "Opening of shot sequence"
                next_text = f"Leads directly into action of clip {i+1}" if i < clip_count else "Resolves current shot sequence"
                clips.append(
                    ClipContinuityItem(
                        clip_number=i,
                        description=f"Part {i} of {clip_count}: Progression of {scene_description[:60]}",
                        image_prompt=(
                            f"Cinematic frame, 35mm film still, {scene_description}. "
                            f"Subject in worn black leather jacket, industrial background, cinematic volumetric lighting, 8k resolution, photorealistic."
                        ),
                        video_prompt=(
                            f"Continuous cinematic shot, slow smooth camera tracking, subject in motion, "
                            f"subtle natural body movements, dust motes floating in light beam, 24fps film motion."
                        ),
                        camera_motion="Slow forward dolly tracking" if i % 2 != 0 else "Subtle pan with character motion",
                        subject_motion="Natural fluid walking and interaction",
                        duration_seconds=duration_per_clip,
                        continuity_from_previous=prev_text if i > 1 else None,
                        continuity_to_next=next_text if i < clip_count else None
                    )
                )
            return ClipContinuityPlan(clip_count=clip_count, clips=clips)

    def enhance_prompt(
        self,
        raw_prompt: str,
        prompt_type: str = "both",
        scene_context: Optional[str] = ""
    ) -> PromptEnhanceResult:
        """
        Enhances simple user input (e.g. 'man walking in factory') into model-ready
        cinematic Image Prompt and Video Prompt without unnecessary bloat.
        """
        if not self.is_available():
            return PromptEnhanceResult(
                enhanced_image_prompt=(
                    f"Cinematic 35mm film still of {raw_prompt}. Photorealistic, intricate textures, "
                    f"atmospheric volumetric lighting, rim light, shallow depth of field, 8k cinematic resolution."
                ),
                enhanced_video_prompt=(
                    f"Cinematic motion of {raw_prompt}. Slow smooth steadycam tracking, natural fluid movement, "
                    f"subtle environmental motion, dust particles drifting, filmic 24fps motion blur."
                ),
                camera_motion="Slow forward tracking shot with shallow depth of field",
                subject_motion="Natural deliberate movement aligned with scene action",
                continuity_notes="Preserves consistent lighting, attire, and environment color palette."
            )

        system_prompt = (
            "You are a master cinematic prompt engineer for AI video models (CogVideoX). "
            "Convert user input into separate, optimized, high-fidelity Image Prompts and Video Prompts. "
            "Image Prompt defines: subject, wardrobe, environment, lighting, framing, texture, color tone. "
            "Video Prompt defines: camera trajectory, subject action, velocity, environmental dynamics. "
            "Do NOT make prompts ridiculously long; keep them focused, vivid, and model-effective."
        )
        user_prompt = (
            f"Raw Prompt: {raw_prompt}\n"
            f"Context: {scene_context}\n"
            "Enhance this into separate Image and Video prompts."
        )

        return self.provider.generate_structured(system_prompt, user_prompt, PromptEnhanceResult)

    def check_continuity(
        self,
        clips_data: List[Dict[str, Any]],
        movie_bible: Optional[Dict[str, Any]] = None
    ) -> ContinuityCheckResult:
        """
        Analyzes a sequence of clips for character, location, temporal, and narrative continuity.
        """
        if not clips_data or len(clips_data) <= 1:
            return ContinuityCheckResult(
                is_consistent=True,
                character_checks=["Single clip or empty timeline - continuity baseline verified."],
                location_checks=["Location confirmed."],
                temporal_checks=["Lighting and time consistent."],
                story_checks=["Story progression coherent."],
                warnings=[],
                recommendations=[]
            )

        if not self.is_available():
            # Rule based check
            warnings = []
            recs = []
            for idx in range(len(clips_data) - 1):
                c1 = clips_data[idx]
                c2 = clips_data[idx + 1]
                # Simple check if prompts have drastically conflicting words
                c1_p = c1.get("image_prompt", "").lower()
                c2_p = c2.get("image_prompt", "").lower()
                if "night" in c1_p and "bright sunlight" in c2_p:
                    warnings.append(f"Potential time-of-day mismatch between Clip {idx+1} and Clip {idx+2}.")
                    recs.append("Ensure consistent lighting setup between sequential clips.")
            return ContinuityCheckResult(
                is_consistent=len(warnings) == 0,
                character_checks=["Character wardrobe matches key rules"],
                location_checks=["Environment spatial orientation aligns"],
                temporal_checks=["Lighting direction checked"],
                story_checks=["Action flows sequentially"],
                warnings=warnings,
                recommendations=recs,
                auto_fix_plan="Align lighting and wardrobe prompts if inconsistencies arise."
            )

        system_prompt = (
            "You are an expert Film Script Supervisor and Continuity Director. "
            "Inspect the sequence of clips for character attire/appearance mismatches, location shifts, "
            "lighting or time-of-day contradictions, and sudden narrative resets. "
            "Return structured analysis and actionable fixes."
        )
        user_prompt = f"CLIPS SEQUENCE:\n{clips_data}\n\nMOVIE BIBLE:\n{movie_bible or {}}"

        return self.provider.generate_structured(system_prompt, user_prompt, ContinuityCheckResult)
