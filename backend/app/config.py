from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


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


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.normalized_image_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
