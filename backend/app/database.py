from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "generation_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    image_hash: Mapped[str] = mapped_column(String(64), index=True)
    prompt: Mapped[str] = mapped_column(String)
    brief: Mapped[dict] = mapped_column(JSON)
    analysis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_request_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TrackRecord(Base):
    __tablename__ = "generated_tracks"

    track_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    duration_seconds: Mapped[int]
    audio_filename: Mapped[str] = mapped_column(String)
    audio_sha256: Mapped[str] = mapped_column(String(64))
    provenance: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


settings = get_settings()
engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()
