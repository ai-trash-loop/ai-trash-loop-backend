from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Repository(Base):
    __tablename__ = "repositories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(500), unique=True)  # GitHub URL, or a local path in dev
    kind: Mapped[str] = mapped_column(String(10))  # "github" | "local"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="repository", order_by="Analysis.id.desc()")


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), index=True)
    status: Mapped[str] = mapped_column(String(10), default="queued")  # queued|running|succeeded|failed
    error: Mapped[str | None] = mapped_column(Text, default=None)
    commit_sha: Mapped[str | None] = mapped_column(String(40), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    summary: Mapped[dict | None] = mapped_column(JSON, default=None)  # denormalized for list views
    report: Mapped[dict | None] = mapped_column(JSON, default=None)  # full AnalysisReport (engine contract)
    repository: Mapped[Repository] = relationship(back_populates="analyses")
