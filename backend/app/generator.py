import hashlib
import math
import struct
import wave
from pathlib import Path

from app.schemas import MusicBrief


class MockGenerator:
    identifier = "mock-wav-generator"
    version = "1.0"
    fixture_identifier = "deterministic-sine-layer-v1"

    def generate(self, *, brief: MusicBrief, prompt: str, output_path: Path) -> str:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = output_path.with_suffix(".tmp")
        sample_rate = 44_100
        duration = brief.duration_seconds
        seed = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
        base_frequency = 180 + (seed % 220)
        second_frequency = base_frequency * (1.5 if brief.energy >= 0.5 else 1.25)
        amplitude = 0.22 + min(brief.energy, 1) * 0.18
        total_samples = sample_rate * duration

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

        tmp_path.replace(output_path)
        return hashlib.sha256(output_path.read_bytes()).hexdigest()
