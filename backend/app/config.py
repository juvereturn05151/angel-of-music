import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _load_local_env() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = backend_root.parent
    _load_env_file(repo_root / ".env")
    _load_env_file(backend_root / ".env")


class Settings(BaseModel):
    app_name: str = "Angel of Music API"
    storage_dir: Path = Path("data")
    normalized_image_dir: Path = Path("data/images")
    audio_dir: Path = Path("data/audio")
    sqlite_path: Path = Path("data/angel_of_music.sqlite3")
    max_image_bytes: int = 5 * 1024 * 1024
    max_image_width: int = 4096
    max_image_height: int = 4096
    max_image_pixels: int = 8_000_000
    visual_analyzer_provider: str = "mock"
    huggingface_api_token: str | None = None
    huggingface_base_url: str = "https://router.huggingface.co/v1"
    huggingface_vision_model: str = "google/gemma-3-4b-it"
    huggingface_timeout_seconds: float = 60.0
    music_generator_provider: str = "mock"
    elevenlabs_api_key: str | None = None
    elevenlabs_base_url: str = "https://api.elevenlabs.io"
    elevenlabs_music_model_id: str = "music_v2"
    elevenlabs_output_format: str = "mp3_48000_192"
    elevenlabs_timeout_seconds: float = 120.0


@lru_cache
def get_settings() -> Settings:
    _load_local_env()
    timeout = os.getenv("HUGGINGFACE_TIMEOUT_SECONDS", "60").strip() or "60"
    vision_model = os.getenv("HUGGINGFACE_VISION_MODEL", "google/gemma-3-4b-it").strip()
    elevenlabs_timeout = os.getenv("ELEVENLABS_TIMEOUT_SECONDS", "120").strip() or "120"
    music_model = os.getenv("ELEVENLABS_MUSIC_MODEL_ID", "music_v2").strip()
    settings = Settings(
        visual_analyzer_provider=os.getenv("VISUAL_ANALYZER_PROVIDER", "mock").strip().lower(),
        huggingface_api_token=os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN"),
        huggingface_base_url=os.getenv(
            "HUGGINGFACE_BASE_URL", "https://router.huggingface.co/v1"
        ).rstrip("/"),
        huggingface_vision_model=vision_model or "google/gemma-3-4b-it",
        huggingface_timeout_seconds=float(timeout),
        music_generator_provider=os.getenv("MUSIC_GENERATOR_PROVIDER", "mock").strip().lower(),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
        elevenlabs_base_url=os.getenv(
            "ELEVENLABS_BASE_URL", "https://api.elevenlabs.io"
        ).rstrip("/"),
        elevenlabs_music_model_id=music_model or "music_v2",
        elevenlabs_output_format=os.getenv(
            "ELEVENLABS_OUTPUT_FORMAT", "mp3_48000_192"
        ).strip(),
        elevenlabs_timeout_seconds=float(elevenlabs_timeout),
    )
    settings.normalized_image_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
