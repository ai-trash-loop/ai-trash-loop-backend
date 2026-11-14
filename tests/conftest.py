from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample"
    (repo / "docs").mkdir(parents=True)
    (repo / "CLAUDE.md").write_text("# Guide\n\nSee [missing](docs/nope.md) and [ok](docs/a.md).\n")
    (repo / "docs" / "a.md").write_text("# A\n")
    return repo


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path/'t.db'}", allow_local_paths=True))
    return TestClient(app)
