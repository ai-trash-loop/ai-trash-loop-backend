# ADR 0001: Backend design for the MVP

Status: Accepted

- **Engine access:** through `EngineClient` (app/services/engine_client.py). The MVP calls the engine in-process as a
  library; an HTTP implementation can replace it without touching routes or the runner. The backend contains no analysis logic.
- **Contract:** `AnalysisReport` is imported from the engine package and used as the response model, so the engine's
  schema is the single source of truth. The frontend generates its types from this backend's `openapi.json`.
- **Jobs:** `POST .../analyses` returns 202 and runs the job as a FastAPI background task; clients poll
  `GET /analyses/{id}`. One active analysis per repository (409 otherwise). A task lost on process restart leaves a
  `running` row; a durable queue is the upgrade path (not needed for the MVP).
- **Untrusted input:** only `https://github.com/<owner>/<repo>` URLs are accepted; clones are shallow, with hooks,
  submodules, symlinks and credentials disabled, a timeout and a size cap, in a temp dir that is always deleted.
  Local paths are accepted only when `ALLOW_LOCAL_PATHS=1` (dev/tests). Public repositories only: no GitHub tokens are handled yet.
- **Storage:** SQLAlchemy 2 with JSON columns (SQLite by default, PostgreSQL via `DATABASE_URL`). Tables are created
  with `create_all`; Alembic migrations are deferred until the schema stabilises.
- **No auth yet:** the API is unauthenticated, so do not expose it publicly as is.
