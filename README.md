# ai-trash-loop-backend

Orchestration API for [AI Trash-Loop](https://github.com/ai-trash-loop): registers repositories, clones them safely,
runs the [analysis engine](https://github.com/ai-trash-loop/ai-trash-loop-engine), stores reports and history.

**Status: not started.** Planned stack: FastAPI, SQLAlchemy, PostgreSQL, Docker. The report contract comes from the
engine's `contracts/analysis_report.schema.json`. See [CLAUDE.md](CLAUDE.md) for conventions.

MIT licensed.
