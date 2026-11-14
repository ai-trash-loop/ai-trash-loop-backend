from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.github import SourceError, parse_github_url
import pytest


def add_repo(client, path) -> dict:
    r = client.post("/api/v1/repositories", json={"url": str(path)})
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_end_to_end_analysis_flow(client, sample_repo):
    repo = add_repo(client, sample_repo)
    assert repo["name"] == "sample" and repo["kind"] == "local" and repo["latest_analysis"] is None

    r = client.post(f"/api/v1/repositories/{repo['id']}/analyses")
    assert r.status_code == 202
    aid = r.json()["id"]

    a = client.get(f"/api/v1/analyses/{aid}").json()  # background task has finished by now (TestClient)
    assert a["status"] == "succeeded", a
    assert a["summary"]["findings_total"] == 1
    assert a["summary"]["findings_by_type"] == {"broken_reference": 1}

    report = client.get(f"/api/v1/analyses/{aid}/report").json()
    assert report["schema_version"] == "0.1.0"
    f = report["findings"][0]
    assert f["type"] == "broken_reference" and f["evidence"][0]["file"] == "CLAUDE.md" and f["evidence"][0]["line_start"] == 3

    assert [x["id"] for x in client.get(f"/api/v1/repositories/{repo['id']}/analyses").json()] == [aid]
    listed = client.get("/api/v1/repositories").json()
    assert listed[0]["latest_analysis"]["id"] == aid


def test_history_accumulates_and_trend_data_present(client, sample_repo):
    repo = add_repo(client, sample_repo)
    for _ in range(2):
        assert client.post(f"/api/v1/repositories/{repo['id']}/analyses").status_code == 202
    hist = client.get(f"/api/v1/repositories/{repo['id']}/analyses").json()
    assert len(hist) == 2 and hist[0]["id"] > hist[1]["id"]


def test_adding_same_repo_twice_is_idempotent(client, sample_repo):
    assert add_repo(client, sample_repo)["id"] == add_repo(client, sample_repo)["id"]


def test_concurrent_analysis_rejected(client, sample_repo):
    repo = add_repo(client, sample_repo)
    from app.models import Analysis

    with client.app.state.session_factory() as db:
        db.add(Analysis(repository_id=repo["id"], status="running"))
        db.commit()
    assert client.post(f"/api/v1/repositories/{repo['id']}/analyses").status_code == 409


def test_failed_analysis_is_recorded_not_raised(client, sample_repo):
    repo = add_repo(client, sample_repo)
    import shutil

    shutil.rmtree(sample_repo)  # source disappears before the job runs
    aid = client.post(f"/api/v1/repositories/{repo['id']}/analyses").json()["id"]
    a = client.get(f"/api/v1/analyses/{aid}").json()
    assert a["status"] == "failed" and a["error"]
    assert client.get(f"/api/v1/analyses/{aid}/report").status_code == 409


def test_unknown_ids_404(client):
    for url in ("/repositories/99", "/analyses/99", "/analyses/99/report", "/repositories/99/analyses"):
        assert client.get("/api/v1" + url).status_code == 404
    assert client.post("/api/v1/repositories/99/analyses").status_code == 404


@pytest.mark.parametrize("bad", [
    "http://github.com/o/r", "https://evil.com/o/r", "https://github.com/o", "https://github.com/o/r/../x",
    "file:///etc", "git@github.com:o/r.git", "https://github.com/o/r;rm -rf", "ext::sh -c id",
])
def test_rejects_non_github_urls(bad):
    with pytest.raises(SourceError):
        parse_github_url(bad)


def test_local_paths_rejected_unless_enabled(tmp_path, sample_repo):
    c = TestClient(create_app(Settings(database_url=f"sqlite:///{tmp_path/'x.db'}")))
    r = c.post("/api/v1/repositories", json={"url": str(sample_repo)})
    assert r.status_code == 422


def test_accepts_valid_github_url_without_cloning(client):
    r = client.post("/api/v1/repositories", json={"url": "https://github.com/ai-trash-loop/ai-trash-loop-engine.git"})
    assert r.status_code == 201 and r.json()["name"] == "ai-trash-loop/ai-trash-loop-engine" and r.json()["kind"] == "github"


def test_timestamps_are_explicit_utc(client, sample_repo):
    repo = add_repo(client, sample_repo)
    assert repo["created_at"].endswith(("Z", "+00:00"))
