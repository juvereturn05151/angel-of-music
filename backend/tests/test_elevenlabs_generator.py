import json
import uuid
from pathlib import Path

import httpx

from app.config import Settings
from app.database import init_db
from app.generator import ElevenMusicGenerator, GenerationProviderError
from app.schemas import GenerationRequest, MusicBrief
from app.services import create_generation_job, get_job, run_generation_job


VALID_MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x64" + (b"\x00" * 1200)


def make_brief(vocals: str = "disabled") -> MusicBrief:
    return MusicBrief.model_validate(
        {
            "narrative_role": "discovery",
            "emotion": "hopeful",
            "textures": ["bright", "warm"],
            "energy": 0.5,
            "emotional_intensity": 0.45,
            "bpm": 96,
            "duration_seconds": 10,
            "instruments": ["piano", "woodwinds"],
            "musical_arc": "gradual-build",
            "loop_requested": True,
            "avoid_terms": ["vocals"],
            "rationale": "test",
            "vocals": vocals,
            "purpose": "temporary background music for game prototype mood communication",
            "custom_narrative_role": None,
            "custom_emotion": None,
        }
    )


def make_settings() -> Settings:
    return Settings(
        elevenlabs_api_key="test-key",
        elevenlabs_base_url="https://api.test.local",
        elevenlabs_music_model_id="music_v2",
        elevenlabs_output_format="mp3_48000_192",
        elevenlabs_timeout_seconds=3,
    )


def make_generator(handler) -> ElevenMusicGenerator:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return ElevenMusicGenerator(settings=make_settings(), client=client)


def test_elevenlabs_success_writes_valid_audio_atomically(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.path == "/v1/music"
        assert request.url.params["output_format"] == "mp3_48000_192"
        assert request.headers["xi-api-key"] == "test-key"
        assert body["model_id"] == "music_v2"
        assert body["music_length_ms"] == 10_000
        assert body["force_instrumental"] is True
        assert body["prompt"] == "purpose: temporary background music vocals: disabled"
        return httpx.Response(200, content=VALID_MP3)

    output_path = tmp_path / "track.mp3"
    result = make_generator(handler).generate(
        brief=make_brief(),
        prompt="purpose: temporary background music vocals: disabled",
        output_path=output_path,
    )

    assert output_path.read_bytes() == VALID_MP3
    assert result.provider == "elevenlabs"
    assert result.model_id == "music_v2"
    assert result.output_format == "mp3_48000_192"
    assert result.audio_hash
    assert not (tmp_path / "track.tmp").exists()


def test_elevenlabs_vocal_enabled_does_not_force_instrumental(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["force_instrumental"] is False
        assert "vocals: enabled" in body["prompt"]
        return httpx.Response(200, content=VALID_MP3)

    make_generator(handler).generate(
        brief=make_brief(vocals="enabled"),
        prompt="purpose: temporary background music vocals: enabled",
        output_path=tmp_path / "track.mp3",
    )


def test_elevenlabs_authentication_failure_is_controlled(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "secret-ish provider details"})

    try:
        make_generator(handler).generate(
            brief=make_brief(), prompt="test", output_path=tmp_path / "track.mp3"
        )
    except GenerationProviderError as exc:
        assert exc.code == "elevenlabs_authentication_failed"
        assert exc.message == "ElevenLabs authentication failed."
        assert "secret-ish" not in exc.message
    else:
        raise AssertionError("Expected authentication failure.")


def test_elevenlabs_timeout_is_controlled(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("provider timeout", request=request)

    try:
        make_generator(handler).generate(
            brief=make_brief(), prompt="test", output_path=tmp_path / "track.mp3"
        )
    except GenerationProviderError as exc:
        assert exc.code == "elevenlabs_timeout"
        assert exc.message == "ElevenLabs music generation timed out."
    else:
        raise AssertionError("Expected timeout failure.")


def test_elevenlabs_rate_limit_is_controlled(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"detail": "quota raw details"})

    try:
        make_generator(handler).generate(
            brief=make_brief(), prompt="test", output_path=tmp_path / "track.mp3"
        )
    except GenerationProviderError as exc:
        assert exc.code == "elevenlabs_rate_limited"
        assert exc.message == "ElevenLabs rate limit was reached."
    else:
        raise AssertionError("Expected rate limit failure.")


def test_elevenlabs_rejected_prompt_is_controlled(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": {"status": "bad_prompt"}})

    try:
        make_generator(handler).generate(
            brief=make_brief(), prompt="test", output_path=tmp_path / "track.mp3"
        )
    except GenerationProviderError as exc:
        assert exc.code == "elevenlabs_prompt_rejected"
        assert exc.message == "ElevenLabs rejected the music prompt."
    else:
        raise AssertionError("Expected rejected prompt failure.")


def test_elevenlabs_invalid_audio_is_rejected_and_partial_file_removed(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"this is not playable audio" * 100)

    output_path = tmp_path / "track.mp3"
    try:
        make_generator(handler).generate(brief=make_brief(), prompt="test", output_path=output_path)
    except GenerationProviderError as exc:
        assert exc.code == "invalid_audio"
        assert exc.message == "Generated MP3 is not playable."
    else:
        raise AssertionError("Expected invalid audio failure.")

    assert not output_path.exists()
    assert not (tmp_path / "track.tmp").exists()


def test_elevenlabs_empty_response_is_rejected_and_partial_file_removed(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"")

    output_path = tmp_path / "track.mp3"
    try:
        make_generator(handler).generate(brief=make_brief(), prompt="test", output_path=output_path)
    except GenerationProviderError as exc:
        assert exc.code == "empty_elevenlabs_response"
        assert exc.message == "ElevenLabs returned no audio."
    else:
        raise AssertionError("Expected empty response failure.")

    assert not output_path.exists()
    assert not (tmp_path / "track.tmp").exists()


def test_provider_error_becomes_controlled_failed_job(monkeypatch) -> None:
    class FailingGenerator:
        output_format = "mp3_48000_192"

        def generate(self, **_) -> None:
            raise GenerationProviderError(
                "elevenlabs_provider_failed",
                "ElevenLabs music generation failed.",
            )

    init_db()
    monkeypatch.setattr("app.services.get_music_generator", lambda: FailingGenerator())
    brief = make_brief()
    job = create_generation_job(
        request=GenerationRequest(
            image_hash="c" * 64,
            prompt="test prompt",
            brief=brief,
            analysis_id=None,
            client_request_id=f"provider-error-job-test-{uuid.uuid4().hex}",
            force_failure=False,
        )
    )

    run_generation_job(job.job_id)
    failed = get_job(job.job_id)

    assert failed is not None
    assert failed.status == "failed"
    assert failed.error == "ElevenLabs music generation failed."
