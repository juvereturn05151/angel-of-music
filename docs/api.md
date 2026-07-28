# API

Base URL during local development: `http://localhost:8000`.

## Endpoints

- `GET /health` returns `{ "status": "ok" }`.
- `POST /api/analyze-image` accepts multipart field `image`; only decoded JPEG, PNG, and WebP are accepted.
- `POST /api/compose-prompt` accepts a `MusicBrief` and returns a deterministic prompt plus warnings.
- `POST /api/generate` accepts `image_hash`, `brief`, `prompt`, optional `analysis_id`, optional `client_request_id`, and optional `force_failure`.
- `GET /api/jobs/{job_id}` returns a persisted job and track metadata when complete.
- `GET /api/tracks/{track_id}` returns track metadata.
- `GET /api/tracks/{track_id}/audio` returns the generated WAV.
- `GET /api/tracks/{track_id}/provenance` returns provenance for the generated track.

## Important Schemas

The backend defines `VisualObservation`, `ArtisticInference`, `MusicBrief`, `AnalysisResponse`, `GenerationRequest`, `GenerationJob`, `GeneratedTrack`, `ProvenanceRecord`, and `ApiError` in `backend/app/schemas.py`.

## Statuses

Generation jobs use `queued`, `generating`, `analyzing`, `complete`, and `failed`.

## Error Handling

Invalid images and missing resources return controlled errors without stack traces. Validation errors use HTTP `422`. Missing jobs or tracks use HTTP `404`.
