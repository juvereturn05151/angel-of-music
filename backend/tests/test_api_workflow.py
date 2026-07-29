import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.schemas import MusicBrief


def make_png(color: tuple[int, int, int] = (120, 160, 220)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_rejects_corrupt_image() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/analyze-image",
        files={"image": ("fake.png", b"not an image", "image/png")},
    )

    assert response.status_code == 400


def test_analyze_compose_generate_workflow() -> None:
    client = TestClient(app)
    with client:
        analysis_response = client.post(
            "/api/analyze-image",
            files={"image": ("scene.png", make_png(), "image/png")},
        )
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        assert analysis["observation"]["image_hash"]
        assert analysis["observation"]["notes"]
        assert analysis["inference"]["duration_seconds"] == 14

        brief = MusicBrief.model_validate({**analysis["inference"], "vocals": "disabled"})
        prompt_response = client.post("/api/compose-prompt", json=brief.model_dump(mode="json"))
        assert prompt_response.status_code == 200
        prompt = prompt_response.json()["prompt"]
        assert "vocals: disabled" in prompt
        assert "rationale:" in prompt

        second_prompt_response = client.post("/api/compose-prompt", json=brief.model_dump(mode="json"))
        assert second_prompt_response.json()["prompt"] == prompt

        generation_response = client.post(
            "/api/generate",
            json={
                "image_hash": analysis["observation"]["image_hash"],
                "brief": brief.model_dump(mode="json"),
                "prompt": prompt,
                "analysis_id": analysis["analysis_id"],
                "client_request_id": "workflow-test-request",
            },
        )
        assert generation_response.status_code == 202
        job = generation_response.json()
        assert job["status"] in {"queued", "complete"}

        duplicate_response = client.post(
            "/api/generate",
            json={
                "image_hash": analysis["observation"]["image_hash"],
                "brief": brief.model_dump(mode="json"),
                "prompt": prompt,
                "analysis_id": analysis["analysis_id"],
                "client_request_id": "workflow-test-request",
            },
        )
        assert duplicate_response.json()["job_id"] == job["job_id"]

        status_response = client.get(f"/api/jobs/{job['job_id']}")
        assert status_response.status_code == 200
        complete_job = status_response.json()
        assert complete_job["status"] == "complete"
        track = complete_job["track"]
        assert track["audio_sha256"]

        audio_response = client.get(track["audio_url"])
        assert audio_response.status_code == 200
        assert audio_response.content.startswith(b"RIFF")

        provenance_response = client.get(f"/api/tracks/{track['track_id']}/provenance")
        assert provenance_response.status_code == 200
        provenance = provenance_response.json()
        assert provenance["image_hash"] == analysis["observation"]["image_hash"]
        assert "audio_hash" in provenance


def test_compose_prompt_can_enable_vocals() -> None:
    client = TestClient(app)
    brief = MusicBrief.model_validate(
        {
            "narrative_role": "character-theme",
            "emotion": "hopeful",
            "textures": ["warm"],
            "energy": 0.45,
            "emotional_intensity": 0.5,
            "bpm": 92,
            "duration_seconds": 12,
            "instruments": ["piano"],
            "musical_arc": "gradual-build",
            "loop_requested": True,
            "avoid_terms": ["vocals", "licensed themes"],
            "rationale": "test",
            "vocals": "enabled",
            "purpose": "temporary menu theme for a character selection screen",
        }
    )

    response = client.post("/api/compose-prompt", json=brief.model_dump(mode="json"))

    assert response.status_code == 200
    payload = response.json()
    assert "purpose: temporary menu theme for a character selection screen" in payload["prompt"]
    assert "vocals: enabled" in payload["prompt"]
    assert "rationale: test" in payload["prompt"]
    assert "avoid: licensed themes" in payload["prompt"]
    assert "vocals were removed" in payload["warnings"][0]


def test_compose_prompt_uses_custom_other_categories() -> None:
    client = TestClient(app)
    brief = MusicBrief.model_validate(
        {
            "narrative_role": "other",
            "custom_narrative_role": "quiet rivalry",
            "emotion": "other",
            "custom_emotion": "bittersweet wonder",
            "textures": ["warm"],
            "energy": 0.45,
            "emotional_intensity": 0.5,
            "bpm": 92,
            "duration_seconds": 12,
            "instruments": ["piano"],
            "musical_arc": "gradual-build",
            "loop_requested": True,
            "avoid_terms": ["vocals"],
            "rationale": "test",
            "vocals": "disabled",
            "purpose": "temporary character cue",
        }
    )

    response = client.post("/api/compose-prompt", json=brief.model_dump(mode="json"))

    assert response.status_code == 200
    prompt = response.json()["prompt"]
    assert "narrative_role: quiet rivalry" in prompt
    assert "emotion: bittersweet wonder" in prompt


def test_compose_prompt_rejects_blank_custom_other_categories() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/compose-prompt",
        json={
            "narrative_role": "other",
            "custom_narrative_role": "",
            "emotion": "other",
            "custom_emotion": "",
            "textures": ["warm"],
            "energy": 0.45,
            "emotional_intensity": 0.5,
            "bpm": 92,
            "duration_seconds": 12,
            "instruments": ["piano"],
            "musical_arc": "gradual-build",
            "loop_requested": True,
            "avoid_terms": ["vocals"],
            "rationale": "test",
            "vocals": "disabled",
            "purpose": "temporary character cue",
        },
    )

    assert response.status_code == 422


def test_controlled_generation_failure() -> None:
    client = TestClient(app)
    with client:
        brief = MusicBrief.model_validate(
            {
                "narrative_role": "danger",
                "emotion": "tense",
                "textures": ["dark"],
                "energy": 0.8,
                "emotional_intensity": 0.8,
                "bpm": 120,
                "duration_seconds": 10,
                "instruments": ["percussion"],
                "musical_arc": "rising-tension",
                "loop_requested": True,
                "avoid_terms": ["vocals"],
                "rationale": "test",
                "vocals": "disabled",
            }
        )
        prompt = client.post("/api/compose-prompt", json=brief.model_dump(mode="json")).json()["prompt"]
        response = client.post(
            "/api/generate",
            json={
                "image_hash": "a" * 64,
                "brief": brief.model_dump(mode="json"),
                "prompt": prompt,
                "force_failure": True,
            },
        )
        job_id = response.json()["job_id"]

        status = client.get(f"/api/jobs/{job_id}").json()

        assert status["status"] == "failed"
        assert "Controlled mock failure" in status["error"]
