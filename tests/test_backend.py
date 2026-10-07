import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import Base, engine, SessionLocal, ensure_schema
from backend.models.db import Project, Scene, Shot, Clip
from backend.schemas.ai import MovieBible, ClipContinuityPlan
from backend.services.ai.director import AIDirector

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    ensure_schema()
    yield

def test_system_diagnostics():
    response = client.get("/api/system/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "python_version" in data
    assert "pytorch_version" in data
    assert "t4_recommended_settings" in data

def test_project_lifecycle():
    # 1. Create Project
    res = client.post("/api/projects", json={
        "name": "The Abandoned Factory",
        "description": "A man explores an old machine in a ruined factory",
        "genre": "Sci-Fi Thriller",
        "visual_style": "Dark cinematic 35mm film"
    })
    assert res.status_code == 200
    proj = res.json()
    proj_id = proj["id"]
    assert proj["name"] == "The Abandoned Factory"

    # 2. Get Project
    res_get = client.get(f"/api/projects/{proj_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == proj_id

    # 3. List Projects
    res_list = client.get("/api/projects")
    assert res_list.status_code == 200
    assert any(p["id"] == proj_id for p in res_list.json())

    # 4. Plan with AI Director (generates Bible and Scenes)
    res_plan = client.post(f"/api/projects/{proj_id}/plan", json={
        "idea": "A man enters an abandoned factory, walks through it, discovers an old machine and turns it on.",
        "genre": "Sci-Fi Mystery"
    })
    assert res_plan.status_code == 200
    plan_data = res_plan.json()
    assert plan_data["status"] == "success"
    assert "movie_bible" in plan_data
    assert plan_data["scenes_created"] > 0

    # 5. Check Scenes
    res_scenes = client.get(f"/api/projects/{proj_id}/scenes")
    assert res_scenes.status_code == 200
    scenes = res_scenes.json()
    assert len(scenes) > 0
    scene_id = scenes[0]["id"]

    # 6. Break Scene into Shots
    res_shots_init = client.post(f"/api/scenes/{scene_id}/break-into-shots")
    assert res_shots_init.status_code == 200
    shot_id = res_shots_init.json()["shot_id"]

    # 7. Test Multi-Clip Decomposition (Requirement #14 & #16 & #72)
    # Test 5 clips
    res_5_clips = client.post(f"/api/shots/{shot_id}/break-into-clips", json={
        "prompt": "A man enters an abandoned factory, walks through it, discovers an old machine and turns it on.",
        "clip_count": 5,
        "duration_per_clip": 5.0
    })
    assert res_5_clips.status_code == 200
    clips_5_data = res_5_clips.json()
    assert clips_5_data["clip_count"] == 5
    assert len(clips_5_data["clips"]) == 5

    # Check each clip has continuity links and separate image/video prompts
    for c in clips_5_data["clips"]:
        assert len(c["image_prompt"]) > 10
        assert len(c["video_prompt"]) > 10
        assert c["duration"] == 5.0

    # Check timeline
    res_timeline = client.get(f"/api/projects/{proj_id}/timeline")
    assert res_timeline.status_code == 200
    timeline_clips = res_timeline.json()
    assert len(timeline_clips) >= 5

    # 8. Test Single Clip Approval & Rejection (Requirement #29 & #30)
    clip_1 = timeline_clips[0]
    clip_2 = timeline_clips[1]

    # Approve Clip 1
    res_app = client.post(f"/api/clips/{clip_1['id']}/approve")
    assert res_app.status_code == 200

    # Reject Clip 2
    res_rej = client.post(f"/api/clips/{clip_2['id']}/reject")
    assert res_rej.status_code == 200

    # Regenerate only Clip 2 (without touching Clip 1 or 3)
    res_regen = client.post(f"/api/clips/{clip_2['id']}/regenerate", json={
        "instructions": "Make camera motion slower and smoother"
    })
    assert res_regen.status_code == 200

    # 9. Test Reordering (Requirement #32)
    reordered_ids = [c["id"] for c in reversed(timeline_clips)]
    res_reorder = client.post("/api/clips/reorder", json={"clip_ids": reordered_ids})
    assert res_reorder.status_code == 200

    # 10. Test Continuity Check
    res_cont = client.post(f"/api/scenes/{scene_id}/check-continuity")
    assert res_cont.status_code == 200
    assert "character_checks" in res_cont.json()

def test_clip_counts_edge_cases():
    """Requirement #72: Test 1 clip, 2 clips, 5 clips, 10 clips."""
    director = AIDirector()
    idea = "A detective searches a dimly lit room and discovers a hidden safe."

    for count in [1, 2, 5, 10]:
        plan = director.break_into_clips(idea, clip_count=count, duration_per_clip=4.0)
        assert plan.clip_count == count
        assert len(plan.clips) == count
        assert plan.clips[0].clip_number == 1
        assert plan.clips[-1].clip_number == count
