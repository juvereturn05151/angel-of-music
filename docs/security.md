# Security Notes

## Image Handling

Uploads are decoded with Pillow instead of trusting extensions. The backend accepts only JPEG, PNG, and WebP, rejects empty/corrupt/oversized images, enforces byte, dimension, and pixel-count limits, uses server-generated filenames, strips metadata by writing normalized PNG files, and records SHA-256 hashes.

## Storage

Runtime images, SQLite data, and generated audio are stored under `backend/data/`, which is ignored by Git. API responses do not expose absolute paths, temporary filenames, secrets, or environment values.

## External Vision API

The default workflow does not send images to an external service. If `VISUAL_ANALYZER_PROVIDER=huggingface`, normalized image content is sent to Hugging Face for visual analysis. The Hugging Face token must stay in local `.env` only and must not be committed. API responses and provenance should not expose the token or local filesystem paths.

## Rights And Usage

Users are responsible for having permission to upload images. Generated mock audio is functional test audio for prototype communication and should not be treated as final licensed soundtrack material.

## Current Limits

This MVP has no authentication or multi-user isolation. It should be run locally only.
