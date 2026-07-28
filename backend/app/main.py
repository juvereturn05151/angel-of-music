from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ValidationError

from app.analysis import VisualAnalyzerError, get_visual_analyzer
from app.config import get_settings
from app.database import init_db
from app.generator import audio_media_type
from app.image_handling import ImageValidationError, validate_and_store_image
from app.prompting import compose_prompt
from app.schemas import (
    AnalysisResponse,
    ApiError,
    GenerationJob,
    GenerationRequest,
    MusicBrief,
    PromptResponse,
)
from app.services import create_generation_job, get_job, get_track, run_generation_job


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="Angel of Music API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.exception_handler(ValidationError)
async def validation_error_handler(_, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ApiError(
            code="validation_error",
            message="The request did not match the required schema.",
            details={"errors": exc.errors()},
        ).model_dump(mode="json"),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/analyze-image", response_model=AnalysisResponse)
async def analyze_image(image: UploadFile = File(...)) -> AnalysisResponse:
    try:
        stored = await validate_and_store_image(image)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    try:
        return get_visual_analyzer().analyze(stored)
    except VisualAnalyzerError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc


@app.post("/api/compose-prompt", response_model=PromptResponse)
def compose_prompt_endpoint(brief: MusicBrief) -> PromptResponse:
    return compose_prompt(brief)


@app.post("/api/generate", response_model=GenerationJob, status_code=202)
def generate(request: GenerationRequest, background_tasks: BackgroundTasks) -> GenerationJob:
    job = create_generation_job(request)
    if job.status == "queued":
        background_tasks.add_task(run_generation_job, job.job_id)
    return job


@app.get("/api/jobs/{job_id}", response_model=GenerationJob)
def job_status(job_id: str) -> GenerationJob:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job was not found.")
    return job


@app.get("/api/tracks/{track_id}")
def track_metadata(track_id: str) -> dict[str, object]:
    track = get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track was not found.")
    return {
        "track_id": track.track_id,
        "job_id": track.job_id,
        "duration_seconds": track.duration_seconds,
        "audio_url": f"/api/tracks/{track.track_id}/audio",
        "audio_filename": track.audio_filename,
        "audio_sha256": track.audio_sha256,
        "created_at": track.created_at,
    }


@app.get("/api/tracks/{track_id}/audio")
def track_audio(track_id: str) -> FileResponse:
    track = get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track was not found.")
    path = (get_settings().audio_dir / track.audio_filename).resolve()
    audio_root = get_settings().audio_dir.resolve()
    if audio_root not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Track audio was not found.")
    return FileResponse(
        path,
        media_type=audio_media_type(track.audio_filename),
        filename=track.audio_filename,
    )


@app.get("/api/tracks/{track_id}/provenance")
def track_provenance(track_id: str) -> dict[str, object]:
    track = get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track was not found.")
    return track.provenance
