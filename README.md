# ai-trash-loop-backend

Orchestration API for [AI Trash-Loop](https://github.com/ai-trash-loop): registers repositories, clones them safely,
runs the [analysis engine](https://github.com/ai-trash-loop/ai-trash-loop-engine), stores reports and history.

## Run locally
```bash
python3 -m venv .venv
.venv/bin/pip install -e ../ai-trash-loop-engine      # or: pip install "trashloop @ git+https://github.com/ai-trash-loop/ai-trash-loop-engine.git"
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/uvicorn app.asgi:app --reload               # http://localhost:8000/docs
```
Set `ALLOW_LOCAL_PATHS=1` to analyze a directory on your machine (dev only). With Docker: `docker compose up --build` (PostgreSQL).

## API (v1)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/repositories` `{url}` | register a GitHub repo (idempotent) |
| GET | `/api/v1/repositories` | list with latest analysis summary |
| POST | `/api/v1/repositories/{id}/analyses` | start an analysis (202; 409 if one is running) |
| GET | `/api/v1/repositories/{id}/analyses` | history, newest first |
| GET | `/api/v1/analyses/{id}` | status + summary |
| GET | `/api/v1/analyses/{id}/report` | full `AnalysisReport` (engine contract) |

`python scripts/export_openapi.py` regenerates `openapi.json`, from which the frontend generates its types.
Design decisions: [docs/adr/](docs/adr/). Limitations: no auth, public repos only, in-process jobs (see ADR 0001).

MIT licensed.
