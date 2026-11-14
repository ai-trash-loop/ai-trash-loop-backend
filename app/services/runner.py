from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.models import Analysis, utcnow
from app.schemas import ReportSummary
from app.services import github
from app.services.engine_client import EngineClient
from trashloop.models import AnalysisReport

log = logging.getLogger("trashloop.runner")


def summarize(report: AnalysisReport) -> ReportSummary:
    return ReportSummary(
        files_scanned=report.metrics.files_scanned,
        est_tokens_total=report.metrics.est_tokens_total,
        est_tokens_duplicated=report.metrics.est_tokens_duplicated,
        findings_total=len(report.findings),
        findings_by_type=dict(Counter(f.type.value for f in report.findings)),
        findings_by_severity=dict(Counter(f.severity.value for f in report.findings)),
    )


def run_analysis(analysis_id: int, sf: sessionmaker[Session], engine: EngineClient, settings: Settings) -> None:
    """Execute one analysis job. Never raises: failures are recorded on the Analysis row."""
    with sf() as db:
        a = db.get(Analysis, analysis_id)
        if a is None:
            return
        a.status, a.started_at = "running", utcnow()
        db.commit()
        repo = a.repository
        try:
            if repo.kind == "local":
                path = Path(repo.source)
                sha = github.head_sha(path)
                report = engine.analyze(path)
            else:
                with github.clone(repo.source, settings.clone_timeout_s, settings.max_clone_mb) as (path, sha):
                    report = engine.analyze(path)
            report.repo.name, report.repo.commit_sha = repo.name, sha
            a.report = report.model_dump(mode="json")
            a.summary = summarize(report).model_dump()
            a.commit_sha, a.status = sha, "succeeded"
        except github.SourceError as e:
            a.status, a.error = "failed", str(e)
        except Exception:  # engine bug or unexpected input: log details server-side, show a generic message
            log.exception("analysis %s failed", analysis_id)
            a.status, a.error = "failed", "Analysis failed unexpectedly"
        a.finished_at = utcnow()
        db.commit()
