"""Safe repository acquisition. Repo contents are untrusted: we clone, read, and never execute anything."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_GITHUB = re.compile(r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$")


class SourceError(ValueError):
    """The requested source is invalid, unreachable, or too large. Message is safe to show to users."""


def parse_github_url(url: str) -> tuple[str, str]:
    m = _GITHUB.match(url.strip())
    if not m:
        raise SourceError("Only https://github.com/<owner>/<repo> URLs are supported")
    return m["owner"], m["repo"]


def _dir_mb(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file() and not f.is_symlink()) / 1_048_576


@contextmanager
def clone(url: str, timeout_s: int, max_mb: int) -> Iterator[tuple[Path, str | None]]:
    """Shallow-clone a public GitHub repo into a temp dir; yield (path, commit_sha); always clean up."""
    owner, repo = parse_github_url(url)
    tmp = Path(tempfile.mkdtemp(prefix="trashloop-"))
    dest = tmp / repo
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp),  # no user git config or credentials
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    cmd = [
        "git", "-c", "protocol.allow=never", "-c", "protocol.https.allow=always",
        "-c", "core.hooksPath=/dev/null", "-c", "core.symlinks=false",
        "clone", "--depth", "1", "--single-branch", "--no-tags", "--no-recurse-submodules", "--quiet",
        f"https://github.com/{owner}/{repo}.git", str(dest),
    ]
    try:
        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            raise SourceError("Cloning timed out") from None
        except subprocess.CalledProcessError:
            raise SourceError("Could not clone repository (is it public and spelled correctly?)") from None
        if _dir_mb(dest) > max_mb:
            raise SourceError(f"Repository is larger than the {max_mb} MB limit")
        yield dest, head_sha(dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def head_sha(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10, check=True,
            env={"PATH": os.environ.get("PATH", ""), "GIT_CONFIG_NOSYSTEM": "1"},
        )
        sha = out.stdout.strip()
        return sha if re.fullmatch(r"[0-9a-f]{40}", sha) else None
    except Exception:
        return None
