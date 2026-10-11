"""The listing against a real git, so the fixture's shape is known to be git's.

Skipped where git is not installed; the coverage gate holds without it, as the knot fidelity
test's does.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from knotview.reading.git_worktrees import GitWorktrees

# Nothing from the surrounding shell may reach these commands: under a commit hook GIT_DIR and
# GIT_INDEX_FILE point at the real repository, and a global config may require signed commits.
CLEAN = {
    **{name: value for name, value in os.environ.items() if not name.startswith("GIT_")},
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _version() -> tuple[int, ...]:
    """The installed git's version, or nothing when git is absent."""
    if shutil.which("git") is None:
        return ()
    said = subprocess.run(
        ["git", "--version"], capture_output=True, text=True, check=False, env=CLEAN
    ).stdout
    found = re.search(r"(\d+)\.(\d+)", said)
    return tuple(int(part) for part in found.groups()) if found else ()


pytestmark = pytest.mark.skipif(
    _version() < (2, 36), reason="needs git 2.36 or later, for worktree list -z"
)


def _git(*arguments: str, cwd: Path) -> None:
    """One git command with a throwaway identity, failing the test if git refuses it."""
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=probe",
            "-c",
            "user.email=probe@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *arguments,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
        env=CLEAN,
    )


def test_a_real_repository_lists_its_worktrees_by_real_path_from_a_symlink_or_a_subdirectory(
    tmp_path: Path,
):
    main = tmp_path / "main"
    (main / "sub").mkdir(parents=True)
    _git("init", "-b", "main", cwd=main)
    _git("commit", "--allow-empty", "-m", "start", cwd=main)
    _git("worktree", "add", "-b", "feature", str(tmp_path / "feature"), cwd=main)
    through = tmp_path / "through"
    through.symlink_to(main)
    expected = [("main", main.resolve()), ("feature", (tmp_path / "feature").resolve())]

    for launch in (through, main / "sub"):
        listed = GitWorktrees(repository=launch).listed()
        assert [(one.name, one.path) for one in listed] == expected
    assert GitWorktrees(repository=through).launch == main.resolve()
