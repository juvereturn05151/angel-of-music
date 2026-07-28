# Angel of Music

Angel of Music is a portfolio full-stack project for game designers who need temporary background music to communicate a scene's intended mood during early prototyping.

The MVP is deliberately human-in-the-loop: upload an image, inspect visual observations, edit every artistic inference, preview a deterministic music prompt, start a persisted generation job, and play the generated audio in the browser.

No API key, local AI model, CUDA, PyTorch, MusicGen, Docker, Redis, Celery, LangChain, authentication, or cloud deployment is required for the default mock workflow. Optional Hugging Face vision analysis and ElevenLabs music generation can be enabled with local `.env` tokens.

## Repository Layout

- `backend/` - Python 3.11, FastAPI, Pydantic v2, SQLAlchemy, SQLite, Pillow, pytest, Ruff.
- `frontend/` - React, TypeScript, Vite, Vitest, React Testing Library.
- `docs/` - Product, architecture, API, security, and manual testing docs.
- `experiments/` - Research notes and prototype scratch space.
- `examples/` - Placeholder evaluation manifests and future sample inputs.

## Setup

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

If your machine reports certificate errors when installing packages, fix the local trusted certificate chain. During verification on this machine, temporary per-command SSL workarounds were needed; they were not written into project config.

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

## Optional Hugging Face Vision Analysis

The app defaults to deterministic mock image analysis. To use Hugging Face with `google/gemma-3-4b-it`, put these values in your local `.env`:

```powershell
VISUAL_ANALYZER_PROVIDER=huggingface
HUGGINGFACE_VISION_MODEL=google/gemma-3-4b-it
HF_TOKEN=your_hugging_face_token_here
```

Make sure your Hugging Face account has accepted the Gemma model license. Restart the backend after changing `.env`.

## Optional ElevenLabs Music Generation

The app defaults to free deterministic mock audio. To generate real instrumental music through Eleven Music v2, put these values in your local `.env`:

```powershell
MUSIC_GENERATOR_PROVIDER=elevenlabs
ELEVENLABS_MUSIC_MODEL_ID=music_v2
ELEVENLABS_OUTPUT_FORMAT=mp3_48000_192
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

The backend sends the final deterministic `MusicBrief` prompt, asks for instrumental-only music with no vocals, and requests the duration from the edited brief. The API key is read only by the backend and is never sent to the frontend.

To switch back to free placeholder audio:

```powershell
MUSIC_GENERATOR_PROVIDER=mock
```

Restart the backend after changing `.env`.

### Paid Smoke Test

This script is opt-in because it calls ElevenLabs and may incur API cost:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts\smoke_elevenlabs_music.py --i-understand-this-costs-money
```

On success, it writes a short audio file under `backend/data/smoke-tests/` and prints non-secret metadata.

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
