from __future__ import annotations

import hashlib
import math
import struct
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from app.config import Settings, get_settings
from app.schemas import MusicBrief


@dataclass(frozen=True)
class GenerationResult:
    audio_hash: str
    provider: str
    model_id: str
    duration_seconds: int
    prompt: str
    output_format: str
    latency_ms: int
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    generator_identifier: str = ""
    generator_version: str = ""
    fixture_identifier: str = ""


class GenerationProviderError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MockGenerator:
    identifier = "mock-wav-generator"
    version = "1.0"
    fixture_identifier = "deterministic-sine-layer-v1"
    output_format = "wav_44100_16"

    def generate(self, *, brief: MusicBrief, prompt: str, output_path: Path) -> GenerationResult:
        started = time.perf_counter()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = output_path.with_suffix(".tmp")
        sample_rate = 44_100
        duration = brief.duration_seconds
        seed = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
        base_frequency = 180 + (seed % 220)
        second_frequency = base_frequency * (1.5 if brief.energy >= 0.5 else 1.25)
        amplitude = 0.22 + min(brief.energy, 1) * 0.18
        total_samples = sample_rate * duration

        try:
            with wave.open(str(tmp_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                for index in range(total_samples):
                    t = index / sample_rate
                    fade_in = min(1.0, t / 0.25)
                    fade_out = min(1.0, (duration - t) / 0.35)
                    envelope = max(0.0, min(fade_in, fade_out))
                    slow_lfo = 0.75 + 0.25 * math.sin(2 * math.pi * 0.25 * t)
                    value = (
                        math.sin(2 * math.pi * base_frequency * t)
                        + 0.45 * math.sin(2 * math.pi * second_frequency * t)
                    )
                    sample = int(max(-1, min(1, value * amplitude * envelope * slow_lfo)) * 32767)
                    wav.writeframes(struct.pack("<h", sample))

            validate_audio_file(tmp_path, self.output_format)
            tmp_path.replace(output_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

        return GenerationResult(
            audio_hash=hashlib.sha256(output_path.read_bytes()).hexdigest(),
            provider="mock",
            model_id="mock",
            duration_seconds=duration,
            prompt=prompt,
            output_format=self.output_format,
            latency_ms=_elapsed_ms(started),
            warnings=["Mock audio is functional test audio, not production music."],
            limitations=[
                "No external AI model was used.",
                "The generated WAV is deterministic mock audio.",
            ],
            generator_identifier=self.identifier,
            generator_version=self.version,
            fixture_identifier=self.fixture_identifier,
        )


class ElevenMusicGenerator:
    identifier = "elevenlabs-music-generator"
    version = "1.0"
    fixture_identifier = "external-elevenlabs-music-v2"

    def __init__(
        self, settings: Settings | None = None, client: httpx.Client | None = None
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client

    @property
    def output_format(self) -> str:
        return self.settings.elevenlabs_output_format

    def generate(self, *, brief: MusicBrief, prompt: str, output_path: Path) -> GenerationResult:
        if not self.settings.elevenlabs_api_key:
            raise GenerationProviderError(
                "missing_elevenlabs_api_key",
                "ElevenLabs music generation is not configured.",
            )

        started = time.perf_counter()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = output_path.with_suffix(".tmp")
        body = {
            "prompt": prompt,
            "music_length_ms": brief.duration_seconds * 1000,
            "model_id": self.settings.elevenlabs_music_model_id,
            "force_instrumental": brief.vocals == "disabled",
        }
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.settings.elevenlabs_api_key,
        }
        close_client = self.client is None
        client = self.client or httpx.Client(timeout=self.settings.elevenlabs_timeout_seconds)

        try:
            with client.stream(
                "POST",
                f"{self.settings.elevenlabs_base_url}/v1/music",
                params={"output_format": self.output_format},
                headers=headers,
                json=body,
            ) as response:
                self._raise_for_status(response)
                bytes_written = 0
                with tmp_path.open("wb") as file:
                    for chunk in response.iter_bytes():
                        if chunk:
                            bytes_written += len(chunk)
                            file.write(chunk)
                if bytes_written == 0:
                    raise GenerationProviderError(
                        "empty_elevenlabs_response",
                        "ElevenLabs returned no audio.",
                    )

            validate_audio_file(tmp_path, self.output_format)
            tmp_path.replace(output_path)
        except GenerationProviderError:
            tmp_path.unlink(missing_ok=True)
            raise
        except httpx.TimeoutException as exc:
            tmp_path.unlink(missing_ok=True)
            raise GenerationProviderError(
                "elevenlabs_timeout",
                "ElevenLabs music generation timed out.",
            ) from exc
        except httpx.RequestError as exc:
            tmp_path.unlink(missing_ok=True)
            raise GenerationProviderError(
                "elevenlabs_request_failed",
                "ElevenLabs music generation could not be reached.",
            ) from exc
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            raise GenerationProviderError(
                "elevenlabs_generation_failed",
                "ElevenLabs music generation failed.",
            ) from exc
        finally:
            if close_client:
                client.close()

        return GenerationResult(
            audio_hash=hashlib.sha256(output_path.read_bytes()).hexdigest(),
            provider="elevenlabs",
            model_id=self.settings.elevenlabs_music_model_id,
            duration_seconds=brief.duration_seconds,
            prompt=prompt,
            output_format=self.output_format,
            latency_ms=_elapsed_ms(started),
            warnings=["External provider output should be reviewed before use."],
            limitations=["Music generation depends on ElevenLabs availability and account limits."],
            generator_identifier=self.identifier,
            generator_version=self.version,
            fixture_identifier=self.fixture_identifier,
        )

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        if response.status_code in {401, 403}:
            raise GenerationProviderError(
                "elevenlabs_authentication_failed",
                "ElevenLabs authentication failed.",
            )
        if response.status_code == 429:
            raise GenerationProviderError(
                "elevenlabs_rate_limited",
                "ElevenLabs rate limit was reached.",
            )
        if response.status_code == 422:
            raise GenerationProviderError(
                "elevenlabs_prompt_rejected",
                "ElevenLabs rejected the music prompt.",
            )
        if response.status_code in {408, 504}:
            raise GenerationProviderError(
                "elevenlabs_timeout",
                "ElevenLabs music generation timed out.",
            )
        raise GenerationProviderError(
            "elevenlabs_provider_failed",
            "ElevenLabs music generation failed.",
        )


def get_music_generator() -> MockGenerator | ElevenMusicGenerator:
    settings = get_settings()
    if settings.music_generator_provider == "elevenlabs":
        return ElevenMusicGenerator(settings=settings)
    if settings.music_generator_provider != "mock":
        raise GenerationProviderError(
            "unknown_music_generator",
            "MUSIC_GENERATOR_PROVIDER must be either 'mock' or 'elevenlabs'.",
        )
    return MockGenerator()


def audio_extension(output_format: str) -> str:
    if output_format.startswith("mp3_"):
        return "mp3"
    if output_format.startswith("wav_"):
        return "wav"
    return "bin"


def audio_media_type(filename: str) -> str:
    if filename.endswith(".mp3"):
        return "audio/mpeg"
    if filename.endswith(".wav"):
        return "audio/wav"
    return "application/octet-stream"


def validate_audio_file(path: Path, output_format: str) -> None:
    data = path.read_bytes()
    if not data:
        raise GenerationProviderError("invalid_audio", "Generated audio was empty.")
    if output_format.startswith("wav_"):
        _validate_wav(path)
        return
    if output_format.startswith("mp3_"):
        _validate_mp3(data)
        return
    raise GenerationProviderError("invalid_audio", "Generated audio format is not supported.")


def _validate_wav(path: Path) -> None:
    try:
        with wave.open(str(path), "rb") as wav:
            if wav.getnframes() <= 0 or wav.getframerate() <= 0:
                raise GenerationProviderError("invalid_audio", "Generated WAV is not playable.")
    except (wave.Error, EOFError) as exc:
        raise GenerationProviderError("invalid_audio", "Generated WAV is not playable.") from exc


def _validate_mp3(data: bytes) -> None:
    if len(data) < 1024:
        raise GenerationProviderError("invalid_audio", "Generated MP3 is too small to be playable.")
    start = 0
    if data.startswith(b"ID3") and len(data) >= 10:
        tag_size = (
            (data[6] & 0x7F) << 21
            | (data[7] & 0x7F) << 14
            | (data[8] & 0x7F) << 7
            | (data[9] & 0x7F)
        )
        start = min(10 + tag_size, len(data) - 2)
    end = min(len(data) - 1, start + 4096)
    for index in range(start, end):
        if data[index] == 0xFF and data[index + 1] & 0xE0 == 0xE0:
            return
    raise GenerationProviderError("invalid_audio", "Generated MP3 is not playable.")


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))
