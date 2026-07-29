# Angel of Music

Angel of Music is a full-stack portfolio project for game designers who need temporary
background music to communicate a scene's intended mood during early prototyping.

The app is human-in-the-loop: upload a scene image, inspect visual observations, edit the
music brief, generate a short track, play it in the browser, and download the result.

## Current Features

- Browser workflow built with React, TypeScript, and Vite.
- Python 3.11+ backend built with FastAPI, Pydantic v2, SQLAlchemy, SQLite, and Pillow.
- Image upload validation for JPEG, PNG, and WebP.
- Mock image analysis for no-secret local demos.
- Optional Hugging Face vision analysis using `google/gemma-3-4b-it`.
- Simplified editable music brief with purpose, mood overview, BPM, duration, loop,
  and vocals.
- Behind-the-scenes deterministic prompt composition from the user-facing brief fields.
- Mock audio fallback for free local testing.
- Optional ElevenLabs Eleven Music v2 generation.
- Vocal control: no vocals forces instrumental-only output; allow vocals permits vocal
  generation when the provider supports it.
- Background generation jobs with status polling.
- Browser playback and generated-track download.
- Backend provenance records for prompt, provider, model, duration, format, latency,
  warnings, limitations, and audio hash.

## Repository Layout

- `backend/` - FastAPI backend, provider integrations, persistence, tests, smoke scripts.
- `frontend/` - React/Vite frontend, UI state, audio player, tests.
- `docs/` - Product, architecture, API, security, decisions, and manual testing docs.
- `experiments/` - Research notes and prototype scratch space.
- `examples/` - Placeholder evaluation manifests and future sample inputs.

## Local Setup

Create local environment files from the example:

```powershell
Copy-Item .env.example .env
```

Install backend dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Install frontend dependencies:

```powershell
cd frontend
npm.cmd install
```

If your machine reports certificate errors when installing packages, fix the local trusted
certificate chain. Temporary SSL workarounds should not be committed to project config.

## Run Locally

Start the backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Start the frontend:

```powershell
cd frontend
npm.cmd run dev
```

Open `http://localhost:5173`.

## Environment Configuration

Local defaults are documented in `.env.example`. Real secrets belong only in `.env` or in
hosting-provider environment variable dashboards.

Backend CORS uses `FRONTEND_ORIGIN`, which can contain multiple comma-separated origins:

```powershell
FRONTEND_ORIGIN=http://localhost:5173,http://127.0.0.1:5173,https://your-frontend.vercel.app
```

Frontend API calls use:

```powershell
VITE_API_BASE_URL=https://your-backend.onrender.com
```

## Optional Hugging Face Vision Analysis

The app defaults to deterministic mock image analysis. To use Hugging Face vision analysis:

```powershell
VISUAL_ANALYZER_PROVIDER=huggingface
HUGGINGFACE_VISION_MODEL=google/gemma-3-4b-it
HUGGINGFACE_BASE_URL=https://router.huggingface.co/v1
HUGGINGFACE_TIMEOUT_SECONDS=60
HF_TOKEN=your_hugging_face_token_here
```

Make sure the Hugging Face account has accepted the Gemma model license. Restart the backend
after changing environment variables.

## Optional ElevenLabs Music Generation

The app defaults to free deterministic mock audio. To generate music through Eleven Music v2:

```powershell
MUSIC_GENERATOR_PROVIDER=elevenlabs
ELEVENLABS_MUSIC_MODEL_ID=music_v2
ELEVENLABS_OUTPUT_FORMAT=mp3_48000_192
ELEVENLABS_BASE_URL=https://api.elevenlabs.io
ELEVENLABS_TIMEOUT_SECONDS=120
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

The backend sends the final deterministic `MusicBrief` prompt and requests the edited
duration, up to 120 seconds. The API key is read only by the backend and is never sent
to the frontend.

To switch back to free placeholder audio:

```powershell
MUSIC_GENERATOR_PROVIDER=mock
```

Restart the backend after changing environment variables.

## Paid Smoke Test

This script is opt-in because it calls ElevenLabs and may incur API cost:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts\smoke_elevenlabs_music.py --i-understand-this-costs-money
```

To test a vocal-enabled brief:

```powershell
python scripts\smoke_elevenlabs_music.py --i-understand-this-costs-money --vocals enabled
```

On success, it writes a short audio file under `backend/data/smoke-tests/` and prints
non-secret metadata.

## Deployment

Recommended deployment shape:

- Backend: Render Web Service from `backend/`
- Frontend: Vercel Vite project from `frontend/`
- Backend URL example: `https://angel-of-music-api.onrender.com`
- Frontend URL example: `https://angel-of-music.vercel.app`
- Custom domain recommendation: `https://angel-of-music.juvetic.com`

Render backend settings:

```text
Root Directory: backend
Build Command: pip install -e .
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render environment should include provider keys, provider settings, `PYTHON_VERSION=3.11.9`,
and `FRONTEND_ORIGIN` with the deployed frontend URL.

Vercel frontend settings:

```text
Root Directory: frontend
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
```

Vercel environment should include:

```text
VITE_API_BASE_URL=https://angel-of-music-api.onrender.com
```

## Free Hosting Limitation

On Render free hosting, persistent disks are not available. The app can still work, but
generated tracks, normalized images, and SQLite job history should be treated as temporary.
Users should download generated tracks during the same active session.

For stronger persistence later, use a Render paid disk or move generated audio to object
storage such as S3, Cloudflare R2, or Supabase Storage.

## Test And Build

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
python -m ruff check app tests
```

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
```
