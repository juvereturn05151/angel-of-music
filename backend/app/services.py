from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database import JobRecord, TrackRecord, get_session, utc_now
from app.generator import MockGenerator
from app.schemas import GeneratedTrack, GenerationJob, GenerationRequest, MusicBrief, ProvenanceRecord


def _job_to_schema(job: JobRecord, track: TrackRecord | None = None) -> GenerationJob:
    generated = None
    if track:
        generated = GeneratedTrack(
            track_id=track.track_id,
            job_id=track.job_id,
            duration_seconds=track.duration_seconds,
            audio_url=f"/api/tracks/{track.track_id}/audio",
            audio_sha256=track.audio_sha256,
            created_at=track.created_at,
        )
    return GenerationJob(
        job_id=job.job_id,
        status=job.status,  # type: ignore[arg-type]
        created_at=job.created_at,
        updated_at=job.updated_at,
        error=job.error,
        track=generated,
    )


def create_generation_job(request: GenerationRequest) -> GenerationJob:
    with get_session() as session:
        if request.client_request_id:
            existing = session.scalar(
                select(JobRecord).where(JobRecord.client_request_id == request.client_request_id)
            )
            if existing:
                track = session.scalar(select(TrackRecord).where(TrackRecord.job_id == existing.job_id))
                return _job_to_schema(existing, track)

        job = JobRecord(
            job_id=uuid.uuid4().hex,
            status="queued",
            image_hash=request.image_hash,
            prompt=request.prompt,
            brief=request.brief.model_dump(mode="json"),
            analysis_id=request.analysis_id,
            client_request_id=request.client_request_id,
            error=None,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        if request.force_failure:
            job.error = "Controlled mock failure requested."
        session.add(job)
        session.commit()
        session.refresh(job)
        return _job_to_schema(job)


def run_generation_job(job_id: str) -> None:
    settings = get_settings()
    generator = MockGenerator()
    with get_session() as session:
        job = session.get(JobRecord, job_id)
        if not job or job.status == "complete":
            return
        try:
            if job.error:
                job.status = "failed"
                job.updated_at = utc_now()
                session.commit()
                return

            job.status = "generating"
            job.updated_at = utc_now()
            session.commit()

            brief = MusicBrief.model_validate(job.brief)
            track_id = uuid.uuid4().hex
            audio_filename = f"{track_id}.wav"
            audio_path = settings.audio_dir / audio_filename
            audio_hash = generator.generate(brief=brief, prompt=job.prompt, output_path=audio_path)

            job.status = "analyzing"
            job.updated_at = utc_now()
            session.commit()

            now = datetime.now(timezone.utc)
            provenance = ProvenanceRecord(
                image_hash=job.image_hash,
                analyzer_identifier="mock-visual-analyzer",
                analyzer_version="1.0",
                analyzer_result={"analysis_id": job.analysis_id, "note": "Stored summary only."},
                user_edited_brief=brief,
                final_prompt=job.prompt,
                generator_identifier=generator.identifier,
                generator_version=generator.version,
                fixture_identifier=generator.fixture_identifier,
                requested_duration=brief.duration_seconds,
                created_at=job.created_at,
                completed_at=now,
                warnings=["Mock audio is functional test audio, not production music."],
                limitations=[
                    "No external AI model was used.",
                    "The generated WAV is deterministic mock audio.",
                ],
                audio_hash=audio_hash,
            )
            track = TrackRecord(
                track_id=track_id,
                job_id=job.job_id,
                duration_seconds=brief.duration_seconds,
                audio_filename=audio_filename,
                audio_sha256=audio_hash,
                provenance=provenance.model_dump(mode="json"),
                created_at=now,
            )
            session.add(track)
            job.status = "complete"
            job.updated_at = utc_now()
            session.commit()
        except Exception:
            job = session.get(JobRecord, job_id)
            if job:
                job.status = "failed"
                job.error = "Mock generation failed in a controlled way."
                job.updated_at = utc_now()
                session.commit()


def get_job(job_id: str) -> GenerationJob | None:
    with get_session() as session:
        job = session.get(JobRecord, job_id)
        if not job:
            return None
        track = session.scalar(select(TrackRecord).where(TrackRecord.job_id == job.job_id))
        return _job_to_schema(job, track)


def get_track(track_id: str) -> TrackRecord | None:
    with get_session() as session:
        track = session.get(TrackRecord, track_id)
        if not track:
            return None
        session.expunge(track)
        return track
