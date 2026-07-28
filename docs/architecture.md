# Architecture

Angel of Music is a local monorepo with a browser frontend and Python backend connected over HTTP.

## Backend

FastAPI exposes the API contracts. Pydantic v2 validates request and response schemas. SQLAlchemy persists generation jobs and generated track metadata in SQLite. Pillow validates image bytes and writes normalized PNG images without metadata. The mock analyzer and mock WAV generator sit behind small provider-neutral classes so real providers can replace them later.

Runtime files live under `backend/data/` and are ignored by Git.

## Frontend

The React/Vite frontend implements one workflow: upload, preview, analyze, edit the brief, preview the deterministic prompt, generate, poll, play audio, and inspect provenance. Audio playback uses a small browser-audio wrapper around an `HTMLAudioElement` plus user-gesture `AudioContext` initialization.

## Job Behavior

Generation uses persisted SQLite state and FastAPI background tasks. Jobs move through `queued`, `generating`, `analyzing`, `complete`, or `failed`. Restart behavior is intentionally simple for the mock MVP: in-process background work is not resumed after a backend restart. Persisted completed jobs and tracks remain available if their files still exist.
