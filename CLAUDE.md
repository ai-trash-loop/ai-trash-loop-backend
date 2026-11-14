# ai-trash-loop-backend

## Purpose
Orchestration API for AI Trash-Loop: registers repositories, clones them safely, runs the engine, stores reports and history, serves the frontend.

## Responsibilities
- OWNS: GitHub integration and cloning, analysis jobs, PostgreSQL persistence, REST API.
- DOES NOT: contain analysis logic. It calls the engine and stores the `AnalysisReport` it returns.

## Stack
Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic, Docker.

## Rules
- The report contract comes from `ai-trash-loop-engine/contracts/analysis_report.schema.json`. Generate models from it; never hand-write or invent report shapes.
- Repo content is untrusted: shallow clone into a temp dir, never execute it, enforce size limits.
- Never log tokens or secrets. Use least-privilege GitHub access.
- Tests for every endpoint. Ask before major architectural decisions. Do not modify unrelated files.
- Decisions go in `docs/adr/`.
