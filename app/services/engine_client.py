"""The backend's only view of the analysis engine (ADR 0001: no analysis logic lives here).

`InProcessEngine` calls the engine as a library. A future `HttpEngine` can implement the same
protocol if the engine is deployed as a separate service; nothing else in the backend changes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from trashloop.analyze import analyze
from trashloop.models import AnalysisReport


class EngineClient(Protocol):
    def analyze(self, path: Path) -> AnalysisReport: ...


class InProcessEngine:
    def analyze(self, path: Path) -> AnalysisReport:
        return analyze(path)  # deterministic stages only; LLM judging is opt-in and not exposed yet
