from __future__ import annotations

import hashlib
import io
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, ImageFile, UnidentifiedImageError

from app.config import get_settings

Image.MAX_IMAGE_PIXELS = get_settings().max_image_pixels
ImageFile.LOAD_TRUNCATED_IMAGES = False


class ImageValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class StoredImage:
    image_id: str
    image_hash: str
    path: Path
    width: int
    height: int
    image_format: str
    dominant_color: str
    brightness: str
    contrast: str
    aspect_ratio: str


def _classify_brightness(mean: float) -> str:
    if mean < 85:
        return "dark"
    if mean > 170:
        return "bright"
    return "balanced"


def _classify_contrast(value: float) -> str:
    if value < 35:
        return "low"
    if value > 85:
        return "high"
    return "moderate"


async def validate_and_store_image(upload: UploadFile) -> StoredImage:
    settings = get_settings()
    content = await upload.read(settings.max_image_bytes + 1)
    await upload.close()
    if not content:
        raise ImageValidationError("empty_image", "Upload an image file with content.")
    if len(content) > settings.max_image_bytes:
        raise ImageValidationError("image_too_large", "Image must be 5 MB or smaller.")

    image_hash = hashlib.sha256(content).hexdigest()

    try:
        with Image.open(io.BytesIO(content)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(content)) as image:
            image.load()
            image_format = image.format
            if image_format not in {"JPEG", "PNG", "WEBP"}:
                raise ImageValidationError(
                    "unsupported_image_type", "Only JPEG, PNG, and WebP images are supported."
                )
            width, height = image.size
            if width <= 0 or height <= 0:
                raise ImageValidationError("invalid_dimensions", "Image dimensions are invalid.")
            if width > settings.max_image_width or height > settings.max_image_height:
                raise ImageValidationError(
                    "image_dimensions_too_large", "Image dimensions exceed the MVP limit."
                )
            if width * height > settings.max_image_pixels:
                raise ImageValidationError("image_pixel_count_too_large", "Image has too many pixels.")

            rgb = image.convert("RGB")
            resized = rgb.resize((1, 1))
            r, g, b = resized.getpixel((0, 0))
            dominant_color = f"#{r:02x}{g:02x}{b:02x}"
            grayscale = rgb.convert("L")
            histogram = grayscale.histogram()
            total = width * height
            mean = sum(i * count for i, count in enumerate(histogram)) / total
            variance = sum(((i - mean) ** 2) * count for i, count in enumerate(histogram)) / total
            contrast = variance**0.5

            normalized_id = uuid.uuid4().hex
            output_path = settings.normalized_image_dir / f"{normalized_id}.png"
            tmp_path = output_path.with_suffix(".tmp")
            rgb.save(tmp_path, format="PNG", optimize=True)
            tmp_path.replace(output_path)
    except ImageValidationError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ImageValidationError("image_pixel_count_too_large", "Image has too many pixels.") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError(
            "invalid_image", "The uploaded file could not be decoded as JPEG, PNG, or WebP."
        ) from exc

    return StoredImage(
        image_id=normalized_id,
        image_hash=image_hash,
        path=output_path,
        width=width,
        height=height,
        image_format=image_format,
        dominant_color=dominant_color,
        brightness=_classify_brightness(mean),
        contrast=_classify_contrast(contrast),
        aspect_ratio=f"{width}:{height}",
    )
