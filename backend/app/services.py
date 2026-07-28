from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database import JobRecord, TrackRecord, get_session, utc_now
from app.generator import GenerationProviderError, audio_extension, get_music_generator
from app.schemas import (
    GeneratedTrack,
    GenerationJob,
    GenerationRequest,
    MusicBrief,
    ProvenanceRecord,
)


def _job_to_schema(job: JobRecord, track: TrackRecord | None = None) -> GenerationJob:
    generated = None
    if track:
        generated = GeneratedTrack(
            track_id=track.track_id,
            job_id=track.job_id,
            duration_seconds=track.duration_seconds,
            audio_url=f"/api/tracks/{track.track_id}/audio",
            audio_filename=track.audio_filename,
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
    generator = get_music_generator()
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
            output_format = getattr(generator, "output_format", "wav_44100_16")
            audio_filename = f"{track_id}.{audio_extension(output_format)}"
            audio_path = settings.audio_dir / audio_filename
            result = generator.generate(brief=brief, prompt=job.prompt, output_path=audio_path)

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
                generator_identifier=result.generator_identifier,
                generator_version=result.generator_version,
                fixture_identifier=result.fixture_identifier,
                requested_duration=result.duration_seconds,
                created_at=job.created_at,
                completed_at=now,
                warnings=[
                    *result.warnings,
                    f"provider: {result.provider}",
                    f"model_id: {result.model_id}",
                    f"duration_seconds: {result.duration_seconds}",
                    f"output_format: {result.output_format}",
                    f"latency_ms: {result.latency_ms}",
                ],
                limitations=result.limitations,
                audio_hash=result.audio_hash,
            )
            provenance_payload = provenance.model_dump(mode="json")
            provenance_payload["provider"] = result.provider
            provenance_payload["model_id"] = result.model_id
            provenance_payload["duration_seconds"] = result.duration_seconds
            provenance_payload["provider_prompt"] = result.prompt
            provenance_payload["output_format"] = result.output_format
            provenance_payload["latency_ms"] = result.latency_ms
            track = TrackRecord(
                track_id=track_id,
                job_id=job.job_id,
                duration_seconds=brief.duration_seconds,
                audio_filename=audio_filename,
                audio_sha256=result.audio_hash,
                provenance=provenance_payload,
                created_at=now,
            )
            session.add(track)
            job.status = "complete"
            job.updated_at = utc_now()
            session.commit()
        except GenerationProviderError as exc:
            job = session.get(JobRecord, job_id)
            if job:
                job.status = "failed"
                job.error = exc.message
                job.updated_at = utc_now()
                session.commit()
        except Exception:
            job = session.get(JobRecord, job_id)
            if job:
                job.status = "failed"
                job.error = "Music generation failed in a controlled way."
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
