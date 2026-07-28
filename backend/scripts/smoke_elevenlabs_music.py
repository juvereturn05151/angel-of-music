from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.generator import ElevenMusicGenerator, audio_extension
from app.prompting import compose_prompt
from app.schemas import MusicBrief


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Opt-in ElevenLabs smoke test. This can incur API cost."
    )
    parser.add_argument(
        "--i-understand-this-costs-money",
        action="store_true",
        help="Required confirmation before the script calls ElevenLabs.",
    )
    args = parser.parse_args()
    if not args.i_understand_this_costs_money:
        print("Refusing to run. Add --i-understand-this-costs-money to call ElevenLabs.")
        return 2

    settings = get_settings()
    if not settings.elevenlabs_api_key:
        print("ELEVENLABS_API_KEY is not set.")
        return 2

    brief = MusicBrief.model_validate(
        {
            "narrative_role": "discovery",
            "emotion": "hopeful",
            "textures": ["bright", "warm", "ethereal"],
            "energy": 0.45,
            "emotional_intensity": 0.4,
            "bpm": 92,
            "duration_seconds": 10,
            "instruments": ["piano", "woodwinds", "bells"],
            "musical_arc": "gradual-build",
            "loop_requested": True,
            "avoid_terms": ["vocals", "licensed themes"],
            "rationale": "Manual smoke test for instrumental background music.",
            "vocals": "disabled",
        }
    )
    prompt = compose_prompt(brief).prompt
    generator = ElevenMusicGenerator(settings=settings)
    extension = audio_extension(settings.elevenlabs_output_format)
    output_path = Path("data") / "smoke-tests" / f"elevenlabs-smoke.{extension}"
    result = generator.generate(brief=brief, prompt=prompt, output_path=output_path)

    print(f"Wrote: {output_path}")
    print(f"Provider: {result.provider}")
    print(f"Model: {result.model_id}")
    print(f"Output format: {result.output_format}")
    print(f"Duration seconds: {result.duration_seconds}")
    print(f"Latency ms: {result.latency_ms}")
    print(f"Audio SHA-256: {result.audio_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
