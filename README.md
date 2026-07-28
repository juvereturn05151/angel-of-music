# Angel of Music

Angel of Music is a portfolio full-stack project for game designers who need temporary background music to communicate a scene's intended mood during early prototyping.

The MVP is deliberately human-in-the-loop: upload an image, inspect mock visual observations, edit every artistic inference, preview a deterministic music prompt, start a persisted mock generation job, and play a short generated WAV in the browser.

No API key, external AI service, local AI model, CUDA, PyTorch, MusicGen, Docker, Redis, Celery, LangChain, authentication, or cloud deployment is required for this milestone.

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
