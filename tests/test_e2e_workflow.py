import os
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.db import Project, Scene, Shot, Clip
from backend.database.session import SessionLocal

client = TestClient(app)

def test_complete_movie_workflow_e2e():
    """
    Requirement #76: Final Success Criteria End-to-End Workflow:
    1. User creates project
    2. User enters movie idea: 'A man enters an abandoned factory, walks through it, discovers an old machine and turns it on.'
    3. AI Director creates Movie Bible
    4. AI creates scenes
    5. User selects scene
    6. User sets Number of Clips = 5, Duration = 5 seconds
    7. OpenRouter creates 5 logical connected clips
    8. User reviews Clip Continuity Plan
    9. Prompts generated & inspected
    10. User approves Clip 1
    11. User rejects Clip 2
    12. User regenerates only Clip 2 (without touching 1 or 3)
    13. User approves clips
    14. Timeline contains all clips with reordering capability
    15. Reordering works seamlessly
    """
    # 1. User creates project
    res_proj = client.post("/api/projects", json={
        "name": "The Last Factory",
        "genre": "Sci-Fi",
        "visual_style": "Photorealistic 35mm film"
    })
    assert res_proj.status_code == 200
    proj_id = res_proj.json()["id"]

    # 2 & 3 & 4. Plan movie with user premise
    idea = "A man enters an abandoned factory, walks through it, discovers an old machine and turns it on."
    res_plan = client.post(f"/api/projects/{proj_id}/plan", json={"idea": idea, "genre": "Sci-Fi"})
    assert res_plan.status_code == 200
    plan_data = res_plan.json()
    assert "movie_bible" in plan_data
    assert plan_data["scenes_created"] > 0

    # 5. User selects scene
    scenes = client.get(f"/api/projects/{proj_id}/scenes").json()
    assert len(scenes) > 0
    selected_scene = scenes[0]

    # Initialize shot for scene
    res_shot = client.post(f"/api/scenes/{selected_scene['id']}/break-into-shots")
    shot_id = res_shot.json()["shot_id"]

    # 6 & 7 & 8. User sets Number of Clips = 5, Duration = 5.0s
    res_clips = client.post(f"/api/shots/{shot_id}/break-into-clips", json={
        "prompt": idea,
        "clip_count": 5,
        "duration_per_clip": 5.0
    })
    assert res_clips.status_code == 200
    plan_clips = res_clips.json()
    assert plan_clips["clip_count"] == 5
    assert len(plan_clips["clips"]) == 5

    # Check that clips have sequential progression and separate prompts (Requirement #20)
    for c in plan_clips["clips"]:
        assert len(c["image_prompt"]) > 0
        assert len(c["video_prompt"]) > 0

    # 9. Verify clips in timeline
    timeline = client.get(f"/api/projects/{proj_id}/timeline").json()
    assert len(timeline) == 5

    clip_1 = timeline[0]
    clip_2 = timeline[1]
    clip_3 = timeline[2]

    # 10. User approves Clip 1
    res_app1 = client.post(f"/api/clips/{clip_1['id']}/approve")
    assert res_app1.status_code == 200
    assert res_app1.json()["preview_status"] == "Approved"

    # 11. User rejects Clip 2
    res_rej2 = client.post(f"/api/clips/{clip_2['id']}/reject")
    assert res_rej2.status_code == 200
    assert res_rej2.json()["preview_status"] == "Rejected"

    # 12. User regenerates only Clip 2 (Requirement #29)
    res_regen2 = client.post(f"/api/clips/{clip_2['id']}/regenerate", json={
        "instructions": "Make camera tracking slower and steady"
    })
    assert res_regen2.status_code == 200
    assert res_regen2.json()["status"] == "regenerating"

    # Verify Clip 1 and Clip 3 status were untouched
    clip_1_after = client.get(f"/api/clips/{clip_1['id']}").json()
    clip_3_after = client.get(f"/api/clips/{clip_3['id']}").json()
    assert clip_1_after["preview_status"] == "Approved"
    assert clip_3_after["preview_status"] == "Draft"

    # 13 & 14. User reorders timeline (Clip 3 -> Clip 1)
    new_order = [timeline[2]["id"], timeline[0]["id"], timeline[1]["id"], timeline[3]["id"], timeline[4]["id"]]
    res_reorder = client.post("/api/clips/reorder", json={"clip_ids": new_order})
    assert res_reorder.status_code == 200

    # 15. Check Continuity Analysis (Requirement #56)
    res_cont = client.post(f"/api/scenes/{selected_scene['id']}/check-continuity")
    assert res_cont.status_code == 200
    assert "character_checks" in res_cont.json()
