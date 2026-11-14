from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Analysis, Repository
from app.schemas import AnalysisOut, RepositoryCreate, RepositoryOut
from app.services import github
from app.services.runner import run_analysis
from trashloop.models import AnalysisReport

router = APIRouter(prefix="/api/v1")


def get_db(request: Request):
    with request.app.state.session_factory() as db:
        yield db


def _repo_out(r: Repository) -> RepositoryOut:
    out = RepositoryOut.model_validate(r, from_attributes=True)
    out.latest_analysis = AnalysisOut.model_validate(r.analyses[0], from_attributes=True) if r.analyses else None
    return out


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/repositories", response_model=RepositoryOut, status_code=201)
def add_repository(body: RepositoryCreate, request: Request, db: Session = Depends(get_db)):
    settings: Settings = request.app.state.settings
    src = body.url.strip()
    if src.startswith("https://"):
        try:
            owner, repo = github.parse_github_url(src)
        except github.SourceError as e:
            raise HTTPException(422, str(e)) from None
        name, source, kind = f"{owner}/{repo}", f"https://github.com/{owner}/{repo}", "github"
    elif settings.allow_local_paths:
        p = Path(src).expanduser()
        if not p.is_dir():
            raise HTTPException(422, "Local path is not a directory")
        name, source, kind = p.resolve().name, str(p.resolve()), "local"
    else:
        raise HTTPException(422, "Only https://github.com/<owner>/<repo> URLs are supported")
    existing = db.scalar(select(Repository).where(Repository.source == source))
    if existing:
        return _repo_out(existing)
    r = Repository(name=name, source=source, kind=kind)
    db.add(r)
    db.commit()
    return _repo_out(r)


@router.get("/repositories", response_model=list[RepositoryOut])
def list_repositories(db: Session = Depends(get_db)):
    return [_repo_out(r) for r in db.scalars(select(Repository).order_by(Repository.id.desc()))]


@router.get("/repositories/{repo_id}", response_model=RepositoryOut)
def get_repository(repo_id: int, db: Session = Depends(get_db)):
    r = db.get(Repository, repo_id)
    if not r:
        raise HTTPException(404, "Repository not found")
    return _repo_out(r)


@router.post("/repositories/{repo_id}/analyses", response_model=AnalysisOut, status_code=202)
def start_analysis(repo_id: int, tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    r = db.get(Repository, repo_id)
    if not r:
        raise HTTPException(404, "Repository not found")
    if any(a.status in ("queued", "running") for a in r.analyses):
        raise HTTPException(409, "An analysis is already in progress for this repository")
    a = Analysis(repository_id=r.id)
    db.add(a)
    db.commit()
    s = request.app.state
    tasks.add_task(run_analysis, a.id, s.session_factory, s.engine_client, s.settings)
    return AnalysisOut.model_validate(a, from_attributes=True)


@router.get("/repositories/{repo_id}/analyses", response_model=list[AnalysisOut])
def list_analyses(repo_id: int, db: Session = Depends(get_db)):
    if not db.get(Repository, repo_id):
        raise HTTPException(404, "Repository not found")
    rows = db.scalars(select(Analysis).where(Analysis.repository_id == repo_id).order_by(Analysis.id.desc()))
    return [AnalysisOut.model_validate(a, from_attributes=True) for a in rows]


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(404, "Analysis not found")
    return AnalysisOut.model_validate(a, from_attributes=True)


@router.get("/analyses/{analysis_id}/report", response_model=AnalysisReport)
def get_report(analysis_id: int, db: Session = Depends(get_db)):
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(404, "Analysis not found")
    if a.status != "succeeded" or a.report is None:
        raise HTTPException(409, f"Report not available (status: {a.status})")
    return AnalysisReport.model_validate(a.report)
