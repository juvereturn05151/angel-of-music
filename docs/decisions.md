# Decisions

## Mock First

This milestone uses deterministic mock analysis and generated WAV fixtures. It does not use external AI services or local AI models. This keeps the project reviewable without keys, GPU setup, or unclear rights.

## Observations Separate From Inferences

Decoded image facts such as size, format, brightness, contrast, and dominant color are separated from editable artistic inference fields. The UI labels the output as mock analysis.

## SQLite And Background Tasks

SQLite is enough for persisted local jobs. FastAPI background tasks keep the API responsive without Redis or Celery. Restart recovery is documented as a limitation.

## Deterministic Prompt Composer

Prompt composition is a pure `MusicBrief -> prompt` function with stable ordering, normalized whitespace, deduplicated terms, no LLM calls, and no provider-specific syntax.
