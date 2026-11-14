from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


def _utc(v: datetime | None) -> datetime | None:
    """SQLite drops tzinfo; all stored timestamps are UTC, so make that explicit in the API."""
    return v.replace(tzinfo=timezone.utc) if v is not None and v.tzinfo is None else v


UtcDatetime = Annotated[datetime, AfterValidator(_utc)]


class RepositoryCreate(BaseModel):
    url: str = Field(description="https://github.com/<owner>/<repo> (or a local path when ALLOW_LOCAL_PATHS=1)")


class ReportSummary(BaseModel):
    files_scanned: int
    est_tokens_total: int = Field(description="ESTIMATE (~4 chars/token) over all discovered markdown files")
    est_tokens_duplicated: int = Field(description="ESTIMATE of tokens in redundant copies")
    findings_total: int
    findings_by_type: dict[str, int]
    findings_by_severity: dict[str, int]


class AnalysisOut(BaseModel):
    id: int
    repository_id: int
    status: str
    error: str | None = None
    commit_sha: str | None = None
    created_at: UtcDatetime
    started_at: UtcDatetime | None = None
    finished_at: UtcDatetime | None = None
    summary: ReportSummary | None = None


class RepositoryOut(BaseModel):
    id: int
    name: str
    source: str
    kind: str
    created_at: UtcDatetime
    latest_analysis: AnalysisOut | None = None
