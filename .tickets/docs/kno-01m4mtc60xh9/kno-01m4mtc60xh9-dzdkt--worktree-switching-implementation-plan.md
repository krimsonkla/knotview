---
id: kno-01m4mtc60xh9-dzdkt
ticket: kno-01m4mtc60xh9
title: Worktree switching implementation plan
type: plan
created: '2026-10-11T07:29:23.570608Z'
updated: '2026-10-11T07:29:23.570608Z'
---

# Worktree Switching Implementation Plan

## Changes Since Last Cycle

Plan gate (findings 230-233 and the voters' notes):
- Task 1: the fake git records its argv, and `listed()` is checked against the pinned argv (231).
  git output is decoded as UTF-8 with replacement, and a path that cannot be decoded or resolved
  is skipped (backend-eng). The real-git test isolates itself from ambient git settings and skips
  below git 2.36 (232, consumer-integration-engineer).
- Task 2: `named` survives a symlink loop (backend-eng). `Backlogs.reading` maps a launch
  subdirectory into the chosen worktree (consumer-integration-engineer, new AC-22).
- Task 3: the default factory is the named `_given`, which a test calls (230). `_way_back` refuses
  a backslash, and `/tags` gains the same test (security-engineer).
- Task 4: CLAUDE.md's Project Structure and digest-poll paragraph are updated (technical-writer).
- The digest scheme now matches the spec's R9 wording (233).

Plan review cycle 1 (235-240): `test_overview_links.py` strips the carried digest; the fake git
moves to `tests/reading/conftest.py` as `fake_git`; pylint-clean assertions; black's one-line
`found.append`; identity asserts in the resolver test; CLAUDE.md's hidden-tab sentence; the three
helpers written in full.

> **For agentic workers:** Execute task by task in order. Steps use checkbox
> (`- [ ]`) syntax for tracking. Read the spec alongside this plan. Do not
> proceed past a STOP step without approval.

**Goal:** From one panel, a reader can read any worktree of the repository's backlog, one at a
time, without restarting anything.
**Architecture:** `GitWorktrees` lists worktrees with `git worktree list --porcelain -z`. A
`Backlogs` resolver maps each request's cookie to one listed worktree, or to the launch directory,
and hands back a cached `Backlog` for it. `Pages` resolves the backlog once per request (listing,
choice, carried digest) instead of holding one. A `/worktree` GET sets the cookie the way `/tags`
does. The frame renders a picker, and `follow.js` takes its baseline from the digest the page
carries.
**Tech Stack:** Python 3.12, FastAPI/Starlette, Jinja2, pytest with pytest-cov (100 percent line
and branch), uv, ruff, black, pylint.
**Spec:** `docs/ai-assistant-ideation/kno-01m4mtc60xh9-worktree-switching-spec.md`
**Test route:** strict. Every task changes behaviour in the panel's application code.

## Global Constraints

- Every route stays a GET. No form, no POST, no write to a backlog, to git or to a worktree.
- Only `src/knotview/reading/knot_command.py` and `src/knotview/reading/git_worktrees.py` may
  contain `subprocess`, `os.system`, `os.popen`, `os.exec`, `os.spawn` or `pty.`.
- git is only ever run as `[git, "-C", <resolved launch>, "worktree", "list", "--porcelain", "-z"]`.
- Never read files under `.git/`. Never open a directory from the cookie without matching it to
  git's current list. Never start git from `/digest`.
- Do not weaken the process-boundary test beyond adding exactly the one module.
- git 2.36 or later is supported. An older git takes the one-worktree fallback silently.
- `panel(backlog)` keeps working with one positional argument. New parameters are keyword-only and
  optional.
- Docstrings explain why, in prose. Test names are sentences, and tests assert rendered content.
- Hold the coverage gate: `uv run pytest` must report 100 percent line and branch coverage.
- Commit subjects are `<type>(<scope>): <description>`. No `Co-Authored-By` or attribution
  trailers (the commit-msg hook rejects them).
- Every commit goes through `dev-gate git commit`.

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/knotview/values/worktree.py` | Create | The `Worktree` value: path, head, branch, `name`, `label`. |
| `src/knotview/reading/git_worktrees.py` | Create | `GitWorktrees`: runs the one listing, parses `-z` porcelain, falls back to the launch directory. |
| `src/knotview/panel/worktree_choice.py` | Create | Cookie name, path encoding, matching a cookie or a typed path to a listed worktree, the containing worktree. |
| `src/knotview/panel/worktrees.py` | Create | `WorktreeSource` protocol, `Alone`, and the `Backlogs` resolver (locked reader cache and last listing). |
| `src/knotview/panel/app.py` | Modify | `Pages` over `Backlogs`; `_backlog(request)`; carried digest; `/worktree`; `_way_back`; `panel()` keyword options. |
| `src/knotview/panel/templates/_worktrees.html` | Create | The picker partial. |
| `src/knotview/panel/templates/layout.html` | Modify | Include the picker; carry the digest on `#live`. |
| `src/knotview/panel/templates/bare.html` | Modify | Include the picker on the unreadable page. |
| `src/knotview/panel/static/follow.js` | Modify | Baseline from `data-digest`. |
| `src/knotview/panel/static/panel.css` | Modify | Picker layout and the marked entry. |
| `src/knotview/entry/console.py` | Modify | Build the panel with `GitWorktrees` and a `KnotCommand` factory. |
| `tests/values/test_worktree.py` | Create | Value naming. |
| `tests/reading/test_git_worktrees.py` | Create | Parsing, fallbacks, pinned argv, through a fake `git`. |
| `tests/reading/conftest.py` | Modify | The `fake_git` fixture beside the fake knot. |
| `tests/reading/test_real_git.py` | Create | Real-git check, skipped without git. |
| `tests/reading/test_knot_command.py` | Modify | The process boundary admits exactly two modules. |
| `tests/panel/test_worktree_choice.py` | Create | Cookie name, encoding, matching, containing, resolver cache and concurrency. |
| `tests/panel/test_worktrees.py` | Create | Picker, choosing, persistence, refusals, digest behaviour, through TestClient. |
| `tests/panel/test_routes.py` | Modify | `/worktree` joins the route table. |
| `tests/panel/test_live.py` | Modify | `follow.js` baseline source. |
| `tests/panel/test_overview_links.py`, `tests/panel/test_tags.py` | Modify | Strip the carried digest; the backslash redirect case. |
| `tests/entry/test_console.py` | Modify | The command passes the worktree source and factory. |
| `CLAUDE.md`, `README.md` | Modify | Architecture, key files, gotchas; the reader-facing paragraph. |

## Coverage

| Spec item | Task(s) |
|-----------|---------|
| R1, R2, R3, R11 | 1 |
| R4 | 3 |
| R5, R6, R7 | 2, 3 |
| R8 | 2 |
| R9, R10 | 2, 3 |
| R12, R14 | 3 |
| R13, R15, R16 | 2, 3 |
| AC-1, AC-2, AC-3, AC-4 | 3 |
| AC-5, AC-6, AC-7 | 3 |
| AC-8, AC-9, AC-10 | 3 |
| AC-11 | 3 |
| AC-12 | 1, 3 |
| AC-13 | 1 |
| AC-14, AC-17, AC-18 | 3 |
| AC-15 | 1, 2, 3 |
| AC-16 | 1 |
| AC-19, AC-20 | 2 |
| AC-22 | 2, 3 |
| AC-21 | 3 |

## Carried Assumptions

- A list as old as the last page render is current enough for the digest poll (MEDIUM). Affects
  Task 2 (`Backlogs.known`) and Task 3 (`Pages.digest`).
- The launch directory is the fallback even when it is a linked worktree or a subdirectory
  (MEDIUM). Affects Task 2 (`Backlogs.reading`, `Backlogs.marked`).
- The cookie name carries a digest of the resolved launch directory (LOW). Affects Task 2.

**Plan-level choices within the spec:**
- The digest for the launch directory stays the bare backlog digest. Any other worktree's digest
  is prefixed with 8 hex characters of its path (spec R9), so `test_live.py` keeps asserting `"d1"`.
- The `Worktree` value has no `main` flag. Nothing reads it, because the launch directory, not the
  main worktree, is the fallback (spec assumption 3).

---

### Task 1: List worktrees with git

**Implements:** R1, R2, R3, R11, AC-12 (reader level), AC-13, AC-15 (real git), AC-16
**Depends on:** none   **Parallel with:** none

**Files:**
- Create: `src/knotview/values/worktree.py`. A new value, because the picker and the resolver both
  need a worktree's name and path.
- Create: `src/knotview/reading/git_worktrees.py`. The second process-starting module, which the
  spec decided on.
- Test: `tests/values/test_worktree.py`, `tests/reading/test_git_worktrees.py`,
  `tests/reading/test_real_git.py`, `tests/reading/conftest.py` (the fake git fixture)
- Modify: `tests/reading/test_knot_command.py`, the boundary test (around lines 254-265)

**Interfaces:**
- Consumes: `knotview.reading.knot_command.PATIENCE` (int, 20).
- Produces:
  - `knotview.values.worktree.Worktree(*, path: Path, head: str = "", branch: str | None = None)`,
    frozen. Properties `name -> str` and `label -> str` (`f"{name} · {path.name}"`).
  - `knotview.reading.git_worktrees.GitWorktrees(*, repository: Path, git: str = "git", patience: int = PATIENCE)`,
    with property `launch -> Path` (resolved), `listed() -> tuple[Worktree, ...]` (never raises,
    never empty), and `_spoken() -> list[str]`.
  - `knotview.reading.git_worktrees.parsed(output: str) -> tuple[Worktree, ...]`
  - Constants `GIT = "git"`, `LISTING = ("worktree", "list", "--porcelain", "-z")`.

**Guardrails:** no other git verb; never read `.git/`; no `shell=True`.

- [ ] **Step 1: Write the failing value test**

`tests/values/test_worktree.py`:
```python
"""How a worktree is named in the picker."""

from pathlib import Path

from knotview.values.worktree import Worktree


def test_a_worktree_on_a_branch_is_named_by_the_branch_without_its_ref_prefix():
    one = Worktree(path=Path("/repo/knotview"), head="a" * 40, branch="refs/heads/jr/feature")

    assert one.name == "jr/feature"
    assert one.label == "jr/feature · knotview"


def test_a_detached_worktree_is_named_by_the_first_seven_characters_of_its_head():
    one = Worktree(path=Path("/repo/review"), head="c1d2e3f4a5b6")

    assert one.name == "c1d2e3f"
    assert one.label == "c1d2e3f · review"
```

- [ ] **Step 2: Write the failing reader tests**

Append to `tests/reading/conftest.py`, beside the fake knot, and add
`from knotview.reading.git_worktrees import GitWorktrees` to its imports:
```python
GIT_SCRIPT = f"""#!{sys.executable}
import os, sys, time
from pathlib import Path

Path(os.environ["KNOTVIEW_FAKE_ARGV"]).write_text("\\0".join(sys.argv[1:]), encoding="utf-8")
mode = os.environ.get("KNOTVIEW_FAKE_GIT", "")
if mode == "hang":
    time.sleep(5)
if mode == "refuse":
    sys.stderr.write("error: unknown switch `z'\\n")
    sys.exit(129)
if mode == "outside":
    sys.stderr.write("fatal: not a git repository\\n")
    sys.exit(128)
if mode == "junk":
    sys.stdout.write("nonsense")
    sys.exit(0)
sys.stdout.buffer.write(Path(os.environ["KNOTVIEW_FAKE_LISTING"]).read_bytes())
"""

GIT_LISTING = (
    "worktree /repo/knotview\0HEAD aaaa\0branch refs/heads/main\0\0"
    "worktree /repo/knotview-feature\0HEAD bbbb\0branch refs/heads/feature\0locked\0\0"
    "worktree /repo/knotview-review\0HEAD c1d2e3f4\0detached\0\0"
)


@pytest.fixture
def fake_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., GitWorktrees]:
    """A GitWorktrees over a fake git that prints a chosen listing or fails a chosen way."""
    script = tmp_path / "git"
    script.write_text(GIT_SCRIPT, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    listing = tmp_path / "listing"
    monkeypatch.setenv("KNOTVIEW_FAKE_ARGV", str(tmp_path / "argv"))

    def build(*, mode: str = "", output: str | bytes = GIT_LISTING) -> GitWorktrees:
        listing.write_bytes(output.encode("utf-8") if isinstance(output, str) else output)
        monkeypatch.setenv("KNOTVIEW_FAKE_GIT", mode)
        monkeypatch.setenv("KNOTVIEW_FAKE_LISTING", str(listing))
        return GitWorktrees(repository=tmp_path, git=str(script), patience=1)

    return build
```

`tests/reading/test_git_worktrees.py`:
```python
"""The worktrees git lists, and the one-directory answer whenever git cannot give them."""

from pathlib import Path

import pytest

from knotview.reading.git_worktrees import GitWorktrees, parsed
from knotview.values.worktree import Worktree


def test_each_record_becomes_a_worktree_in_the_order_git_lists_them(fake_git):
    listed = fake_git().listed()

    assert [(one.name, one.path) for one in listed] == [
        ("main", Path("/repo/knotview")),
        ("feature", Path("/repo/knotview-feature")),
        ("c1d2e3f", Path("/repo/knotview-review")),
    ]


def test_bare_and_prunable_worktrees_are_not_offered():
    output = (
        "worktree /repo/bare.git\0bare\0\0"
        "worktree /repo/knotview\0HEAD aaaa\0branch refs/heads/main\0\0"
        "worktree /repo/gone\0HEAD bbbb\0branch refs/heads/old\0"
        "prunable gitdir file points to non-existent location\0\0"
    )

    assert [one.path for one in parsed(output)] == [Path("/repo/knotview")]


def test_a_record_that_does_not_open_with_its_path_makes_the_whole_listing_unread():
    assert not parsed("HEAD aaaa\0branch refs/heads/main\0\0")
    assert not parsed("worktree\0\0")


@pytest.mark.parametrize("mode", ["refuse", "outside", "junk", "hang"])
def test_a_git_that_cannot_answer_leaves_the_launch_directory_alone(fake_git, tmp_path, mode):
    """An older git refusing -z, a directory that is not a repository, output of another shape,
    and a git that never answers all read the same: one worktree, so no picker."""
    assert fake_git(mode=mode).listed() == (Worktree(path=tmp_path.resolve()),)


def test_a_listing_with_nothing_offered_leaves_the_launch_directory_alone(fake_git, tmp_path):
    assert fake_git(output="worktree /repo/bare.git\0bare\0\0").listed() == (
        Worktree(path=tmp_path.resolve()),
    )


def test_a_missing_git_leaves_the_launch_directory_alone(tmp_path):
    missing = GitWorktrees(repository=tmp_path, git=str(tmp_path / "absent"))

    assert missing.listed() == (Worktree(path=tmp_path.resolve()),)


def test_git_is_only_ever_asked_to_list_worktrees_in_the_resolved_launch_directory(
    fake_git, tmp_path
):
    reader = fake_git()

    reader.listed()

    assert reader.launch == tmp_path.resolve()
    assert (tmp_path / "argv").read_text(encoding="utf-8").split("\0") == [
        "-C",
        str(tmp_path.resolve()),
        "worktree",
        "list",
        "--porcelain",
        "-z",
    ]


def test_a_path_git_prints_that_is_not_utf8_is_left_out_and_the_rest_offered(fake_git):
    output = (
        b"worktree /repo/\xff\0HEAD aaaa\0detached\0\0"
        b"worktree /repo/knotview\0HEAD bbbb\0branch refs/heads/main\0\0"
        b"worktree /repo/knotview-feature\0HEAD cccc\0branch refs/heads/feature\0\0"
    )

    assert [one.name for one in fake_git(output=output).listed()] == ["main", "feature"]


def test_a_path_caught_in_a_symlink_loop_is_left_out(tmp_path):
    loop = tmp_path / "loop"
    loop.symlink_to(loop)
    output = f"worktree {loop}\0HEAD aaaa\0detached\0\0worktree /repo/knotview\0HEAD bbbb\0\0"

    assert [one.path for one in parsed(output)] == [Path("/repo/knotview")]
```

`tests/reading/test_real_git.py`:
```python
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
```

In `tests/reading/test_knot_command.py`, change the boundary test's docstring and assertion:
```python
def test_only_the_command_modules_reach_outside_the_process():
    """The read-only guarantee is structural: knot is invoked in one module, git in one other,
    every knot verb comes from READS, and git is only ever asked to list worktrees. So the guard
    is on who may run a process at all, not on which words appear in the package: "status" is
    also a field name."""
    source = Path(__import__("knotview").__file__).resolve().parent
    spawning = ("subprocess", "os.system", "os.popen", "os.exec", "os.spawn", "pty.")
    running = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*.py")
        if any(token in path.read_text(encoding="utf-8") for token in spawning)
    }
    assert running == {"reading/knot_command.py", "reading/git_worktrees.py"}
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest --no-cov tests/values/test_worktree.py tests/reading/test_git_worktrees.py tests/reading/test_real_git.py tests/reading/test_knot_command.py -q`
Expected: collection errors with `ModuleNotFoundError: No module named 'knotview.values.worktree'`
(and `knotview.reading.git_worktrees`). The boundary test fails on the set.

- [ ] **Step 4: Write the value**

`src/knotview/values/worktree.py`:
```python
"""One working tree of a repository, as git lists it."""

from dataclasses import dataclass
from pathlib import Path

# git names a branch by its full ref; a reader knows it by the part after this.
BRANCHES = "refs/heads/"

# How much of a detached head names it, which is git's own short form.
SHORT_HEAD = 7


@dataclass(frozen=True, kw_only=True)
class Worktree:
    """A checkout of the repository: where it is, and what it has checked out.

    Each one holds its own copy of the backlog, because knot keeps tickets inside the checkout.
    The path is resolved by whoever makes one, so two spellings of one directory are one worktree.
    """

    path: Path
    head: str = ""
    branch: str | None = None

    @property
    def name(self) -> str:
        """The branch without its ref prefix, or the head's short form when nothing is checked out
        by name."""
        if self.branch:
            return self.branch.removeprefix(BRANCHES)
        return self.head[:SHORT_HEAD]

    @property
    def label(self) -> str:
        """What the picker shows. Both halves, since two worktrees can share either one."""
        return f"{self.name} · {self.path.name}"
```

- [ ] **Step 5: Write the reader**

`src/knotview/reading/git_worktrees.py`:
```python
"""The repository's worktrees, read by asking git to list them."""

import subprocess
from pathlib import Path

from knotview.reading.knot_command import PATIENCE
from knotview.values.worktree import Worktree

# The command, named for the same reason knot's is: the second and last place this panel reaches
# outside itself is one constant somebody can see.
GIT = "git"

# The one thing git is ever asked. It lists and changes nothing, and -z ends every field with a
# NUL, so a path holding a space or a newline arrives whole. It needs git 2.36 or later; an older
# git refuses the option, which reads the same as git not answering.
LISTING = ("worktree", "list", "--porcelain", "-z")

# The labels git puts on a worktree no backlog can be read from: a bare repository has no checkout,
# and a prunable worktree's directory is gone.
UNREADABLE = ("bare", "prunable")

# What a byte that is not UTF-8 decodes to. A path holding one cannot be named faithfully, so the
# worktree it belongs to is left out rather than offered under a name that opens nothing.
UNDECODABLE = "\ufffd"


class GitWorktrees:
    """The worktrees of the repository the panel was started in, or that directory alone.

    Never a refusal. Worktrees are a convenience on top of a panel that already works over one
    directory, so git missing, too old, pointed at something that is not a repository, wedged, or
    answering in a shape this does not know all mean one thing: there is one worktree, the one the
    panel was started in, and the panel looks as it did before it knew about worktrees.
    """

    def __init__(self, *, repository: Path, git: str = GIT, patience: int = PATIENCE) -> None:
        self._launch = repository.resolve()
        self._git = git
        self._patience = patience

    @property
    def launch(self) -> Path:
        """The directory the panel was started in, resolved, which answers when git cannot."""
        return self._launch

    def listed(self) -> tuple[Worktree, ...]:
        """Every worktree git offers a backlog in, in git's order, or the launch directory alone."""
        try:
            answer = subprocess.run(
                self._spoken(),
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=self._patience,
            )
        except (OSError, subprocess.TimeoutExpired):
            return self._alone()
        if answer.returncode != 0:
            return self._alone()
        return parsed(answer.stdout) or self._alone()

    def _spoken(self) -> list[str]:
        """The argument list git is handed: the repository by -C, then the one listing."""
        return [self._git, "-C", str(self._launch), *LISTING]

    def _alone(self) -> tuple[Worktree, ...]:
        """The launch directory as the only worktree."""
        return (Worktree(path=self._launch),)


def parsed(output: str) -> tuple[Worktree, ...]:
    """git's NUL-separated records as worktrees, or nothing if any record is not one.

    A record is a run of "label value" fields ended by an empty field. One that does not open with
    its worktree's path is a shape this was not written for, and guessing at the rest could offer
    the reader a directory git never named.
    """
    found: list[Worktree] = []
    for record in output.split("\0\0"):
        fields = [one for one in record.split("\0") if one]
        if not fields:
            continue
        label, _, path = fields[0].partition(" ")
        if label != "worktree" or not path:
            return ()
        held = dict(one.partition(" ")[::2] for one in fields[1:])
        if any(mark in held for mark in UNREADABLE) or UNDECODABLE in path:
            continue
        try:
            resolved = Path(path).resolve()
        except (OSError, RuntimeError):
            # A symlink loop: Python 3.12 raises RuntimeError for it, later versions OSError.
            continue
        found.append(Worktree(path=resolved, head=held.get("HEAD", ""), branch=held.get("branch")))
    return tuple(found)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest --no-cov tests/values/test_worktree.py tests/reading/test_git_worktrees.py tests/reading/test_real_git.py tests/reading/test_knot_command.py -q`
Expected: all pass. `test_real_git.py` is skipped only where git is absent or older than 2.36.

- [ ] **Step 7: Run the task's full verification**

Run: `uv run pytest && uv run ruff check src tests && uv run black --check src tests && uv run pylint src tests`
Expected: the suite passes with `Required test coverage of 100% reached`. ruff and black are clean,
and pylint scores 10.00/10.

- [ ] **Step 8: Commit**
```bash
git add src/knotview/values/worktree.py src/knotview/reading/git_worktrees.py tests/values/test_worktree.py tests/reading/conftest.py tests/reading/test_git_worktrees.py tests/reading/test_real_git.py tests/reading/test_knot_command.py
dev-gate git commit -m "feat(reading): list a repository's worktrees through git (kno-01m4mtc60xh9)"
```

---

### Task 2: Choose a worktree and resolve its backlog

**Implements:** R5 and R6 (matching), R8, R10 (`known`), R13, R15, R16, AC-15 (containing),
AC-19, AC-20, AC-22
**Depends on:** Task 1   **Parallel with:** none

**Files:**
- Create: `src/knotview/panel/worktree_choice.py`. Mirrors `tags.py`: one module owns the cookie.
- Create: `src/knotview/panel/worktrees.py`. The resolver the spec names. It holds shared state
  that `Pages` should not own.
- Test: `tests/panel/test_worktree_choice.py`

**Interfaces:**
- Consumes: `Worktree` (Task 1); `knotview.reading.backlog.Backlog`.
- Produces:
  - `worktree_choice.PREFIX = "knotview_worktree_"`
  - `worktree_choice.cookie_name(launch: Path) -> str`
  - `worktree_choice.encoded(path: Path) -> str`
  - `worktree_choice.named(text: str, among: tuple[Worktree, ...]) -> Worktree | None`
  - `worktree_choice.chosen(held: str | None, among: tuple[Worktree, ...]) -> Worktree | None`
  - `worktree_choice.containing(launch: Path, among: tuple[Worktree, ...]) -> Worktree | None`
  - `worktrees.WorktreeSource` (Protocol: property `launch -> Path`, `listed() -> tuple[Worktree, ...]`)
  - `worktrees.Alone(launch: Path)`, a `WorktreeSource` with one worktree.
  - `worktrees.Backlogs(*, launch: Backlog, source: WorktreeSource, opened: Callable[[Path], Backlog])`
    with attribute `cookie: str`, property `launch -> Path`, and methods
    `refreshed() -> tuple[Worktree, ...]`, `known() -> tuple[Worktree, ...]`,
    `reading(held: str | None, among: tuple[Worktree, ...]) -> tuple[Path, Backlog]`,
    `marked(held: str | None, among: tuple[Worktree, ...]) -> Path | None`, and
    `stamped(path: Path, digest: str) -> str`.

**Guardrails:** a cookie or typed path is used only after it matches a listed worktree. A NUL in a
cookie must not raise.

- [ ] **Step 1: Write the failing tests**

`tests/panel/test_worktree_choice.py`:
```python
"""Which worktree a cookie picks, and the readers kept for each."""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from knotview.panel.worktree_choice import (
    PREFIX,
    chosen,
    containing,
    cookie_name,
    encoded,
    named,
)
from knotview.panel.worktrees import Alone, Backlogs, WorktreeSource
from knotview.values.worktree import Worktree
from tests.panel.declared import DeclaredBacklog

MAIN = Worktree(path=Path("/repo/knotview"), branch="refs/heads/main")
NESTED = Worktree(path=Path("/repo/knotview/nested"), branch="refs/heads/nested")
AWKWARD = Worktree(path=Path('/repo/my wt, x; "é"'), branch="refs/heads/odd")
LISTED = (MAIN, NESTED, AWKWARD)


class Listed:  # pylint: disable=too-few-public-methods
    """A worktree source over LISTED, launched in the main worktree."""

    launch = MAIN.path

    def listed(self) -> tuple[Worktree, ...]:
        """The declared worktrees."""
        return LISTED


def _unused(path: Path) -> DeclaredBacklog:
    """A factory for tests that never make a reader for a new path."""
    raise AssertionError(f"no reader should be made for {path}")


def test_two_launch_directories_get_two_cookie_names_under_one_prefix():
    one, other = cookie_name(Path("/repo/a")), cookie_name(Path("/repo/b"))

    assert one != other
    assert one.startswith(PREFIX) and other.startswith(PREFIX)


def test_any_path_survives_the_cookie_and_picks_its_worktree():
    held = encoded(AWKWARD.path)

    assert all(mark not in held for mark in ' ,;"')
    assert chosen(held, LISTED) == AWKWARD


def test_a_cookie_or_path_that_names_no_listed_worktree_picks_nothing():
    assert chosen(encoded(Path("/elsewhere")), LISTED) is None
    assert chosen(None, LISTED) is None
    assert chosen("", LISTED) is None
    assert chosen("%00", LISTED) is None
    assert named("", LISTED) is None


def test_a_typed_path_is_matched_after_resolving():
    assert named("/repo/knotview/nested/..", LISTED) == MAIN


def test_a_path_caught_in_a_symlink_loop_names_nothing(tmp_path):
    loop = tmp_path / "loop"
    loop.symlink_to(loop)

    assert named(str(loop), LISTED) is None


def test_the_launch_directory_belongs_to_the_deepest_worktree_that_holds_it():
    assert containing(Path("/repo/knotview/nested/src"), LISTED) == NESTED
    assert containing(Path("/repo/knotview/docs"), LISTED) == MAIN
    assert containing(Path("/elsewhere"), LISTED) is None


def test_a_request_reads_the_chosen_worktree_or_else_the_launch_directory():
    launch, nested = DeclaredBacklog(), DeclaredBacklog()
    backlogs = Backlogs(launch=launch, source=Listed(), opened=lambda path: nested)

    read_nested = backlogs.reading(encoded(NESTED.path), LISTED)
    read_elsewhere = backlogs.reading(encoded(Path("/elsewhere")), LISTED)

    assert read_nested[0] == NESTED.path and read_nested[1] is nested
    assert read_elsewhere[0] == MAIN.path and read_elsewhere[1] is launch
    assert backlogs.marked(None, LISTED) == MAIN.path
    assert backlogs.marked(encoded(NESTED.path), LISTED) == NESTED.path


def test_a_launch_below_a_worktree_root_reads_the_same_place_in_the_chosen_worktree():
    other = Worktree(path=Path("/repo/other"), branch="refs/heads/other")
    made: list[Path] = []

    class Below:  # pylint: disable=too-few-public-methods
        """Launched in a subdirectory of the main worktree."""

        launch = MAIN.path / "tools" / "board"

        def listed(self) -> tuple[Worktree, ...]:
            """Main and one other."""
            return (MAIN, other)

    backlogs = Backlogs(
        launch=DeclaredBacklog(),
        source=Below(),
        opened=lambda path: made.append(path) or DeclaredBacklog(),
    )

    assert backlogs.reading(encoded(other.path), (MAIN, other))[0] == other.path / "tools" / "board"
    assert backlogs.reading(encoded(MAIN.path), (MAIN, other))[0] == Below.launch
    assert backlogs.reading(encoded(other.path), (other,))[0] == other.path
    assert made == [other.path / "tools" / "board", other.path]


def test_nothing_is_marked_when_the_launch_directory_is_in_no_listed_worktree():
    backlogs = Backlogs(launch=DeclaredBacklog(), source=Alone(Path("/elsewhere")), opened=_unused)

    assert backlogs.marked(None, LISTED) is None


def test_the_digest_sees_no_listing_until_a_page_has_refreshed_it():
    backlogs = Backlogs(launch=DeclaredBacklog(), source=Listed(), opened=_unused)

    assert not backlogs.known()
    assert backlogs.refreshed() == LISTED
    assert backlogs.known() == LISTED


def test_the_launch_digest_is_unchanged_and_any_other_worktree_s_is_told_apart():
    backlogs = Backlogs(launch=DeclaredBacklog(), source=Listed(), opened=_unused)

    assert backlogs.stamped(MAIN.path, "d1") == "d1"
    assert backlogs.stamped(NESTED.path, "d1").endswith(".d1")
    assert backlogs.stamped(NESTED.path, "d1") != backlogs.stamped(AWKWARD.path, "d1")


def test_concurrent_first_reads_of_one_worktree_make_exactly_one_reader():
    made: list[Path] = []

    def opened(path: Path) -> DeclaredBacklog:
        made.append(path)
        time.sleep(0.01)
        return DeclaredBacklog()

    backlogs = Backlogs(launch=DeclaredBacklog(), source=Listed(), opened=opened)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: backlogs.reading(encoded(NESTED.path), LISTED), range(16)))

    assert made == [NESTED.path]


def test_the_worktree_source_port_itself_answers_nothing():
    """Refusals, not defaults, as the Backlog port's are."""
    with pytest.raises(NotImplementedError):
        WorktreeSource.listed(object())
    with pytest.raises(NotImplementedError):
        WorktreeSource.launch.fget(object())


def test_alone_offers_its_resolved_launch_directory_and_nothing_else(tmp_path):
    alone = Alone(tmp_path / ".")

    assert alone.launch == tmp_path.resolve()
    assert alone.listed() == (Worktree(path=tmp_path.resolve()),)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest --no-cov tests/panel/test_worktree_choice.py -q`
Expected: collection error `ModuleNotFoundError: No module named 'knotview.panel.worktree_choice'`.

- [ ] **Step 3: Write the choice module**

`src/knotview/panel/worktree_choice.py`:
```python
"""Which worktree a reader has chosen, and how the choice travels in their browser."""

import hashlib
from pathlib import Path
from urllib.parse import quote, unquote

from knotview.values.worktree import Worktree

# The cookie's name before its suffix. A cookie because the choice is the reader's, like their
# tags: it lives in their browser and is never written anywhere the panel reads tickets from.
PREFIX = "knotview_worktree_"


def cookie_name(launch: Path) -> str:
    """The cookie for one panel's choice, named for the directory the panel was started in.

    A browser sends a host's cookies to every port on it, so two panels over two repositories would
    otherwise overwrite each other's choice. The suffix is a digest of the resolved launch
    directory, which is known whether or not git answers.
    """
    return PREFIX + hashlib.sha256(str(launch.resolve()).encode("utf-8")).hexdigest()[:12]


def encoded(path: Path) -> str:
    """A path as a cookie carries it, with every character outside the unreserved set escaped.

    A worktree can live under a path with spaces, commas, semicolons, quotes or any script, and a
    cookie value cannot hold most of those as they are.
    """
    return quote(str(path), safe="")


def named(text: str, among: tuple[Worktree, ...]) -> Worktree | None:
    """The listed worktree a path names, after resolving, or nothing.

    Never trusted on its own: the path picks the directory knot is run in, and anyone can edit a
    cookie or a link. A blank names nothing rather than the working directory, and a path that
    cannot be a path (it holds a NUL, or loops) names nothing rather than failing the page.
    """
    if not text:
        return None
    try:
        wanted = Path(text).resolve()
    except (ValueError, OSError, RuntimeError):
        # A NUL in the text, or a symlink loop (RuntimeError on Python 3.12, OSError later).
        return None
    return next((one for one in among if one.path == wanted), None)


def chosen(held: str | None, among: tuple[Worktree, ...]) -> Worktree | None:
    """The listed worktree a cookie names, or nothing for a cookie that names no listed one."""
    return named(unquote(held or ""), among)


def containing(launch: Path, among: tuple[Worktree, ...]) -> Worktree | None:
    """The deepest listed worktree the launch directory is in, or nothing if it is in none.

    A panel started in a subdirectory of a checkout is reading that checkout, so that is the entry
    the picker marks; a worktree nested inside another wins, being the nearer one.
    """
    holding = [one for one in among if launch.is_relative_to(one.path)]
    return max(holding, key=lambda one: len(one.path.parts), default=None)
```

- [ ] **Step 4: Write the resolver**

`src/knotview/panel/worktrees.py`:
```python
"""Which backlog a request reads: the chosen worktree's, or the launch directory's."""

import hashlib
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from knotview.panel.worktree_choice import chosen, containing, cookie_name
from knotview.reading.backlog import Backlog
from knotview.values.worktree import Worktree


class WorktreeSource(Protocol):
    """Where worktrees come from: git for the command, a declared list for a test."""

    @property
    def launch(self) -> Path:
        """The directory the panel was started in, resolved."""
        raise NotImplementedError

    def listed(self) -> tuple[Worktree, ...]:
        """Every worktree offered, or the launch directory alone; never empty, never a refusal."""
        raise NotImplementedError


class Alone:
    """One worktree and nothing to ask: the panel built over one backlog, as the tests build it."""

    def __init__(self, launch: Path) -> None:
        self._launch = launch.resolve()

    @property
    def launch(self) -> Path:
        """The one directory."""
        return self._launch

    def listed(self) -> tuple[Worktree, ...]:
        """The one directory as the only worktree."""
        return (Worktree(path=self._launch),)


class Backlogs:
    """One backlog reader per worktree, and which one a request's cookie picks.

    Page handlers run in the thread pool, so the readers and the last listing are shared between
    threads. Both sit behind one lock: a reader is made at most once per path, and a listing is
    replaced whole. Pages refresh the listing, since a page render already starts processes. The
    digest only reads it, because every open tab asks for the digest about once a second, and a git
    process per tick per tab is the cost the digest exists to avoid.
    """

    def __init__(
        self,
        *,
        launch: Backlog,
        source: WorktreeSource,
        opened: Callable[[Path], Backlog],
    ) -> None:
        self._source = source
        self._opened = opened
        self._lock = threading.Lock()
        self._readers: dict[Path, Backlog] = {source.launch: launch}
        self._listed: tuple[Worktree, ...] = ()
        self.cookie = cookie_name(source.launch)

    @property
    def launch(self) -> Path:
        """The directory the panel was started in, which every unmatched choice falls back to."""
        return self._source.launch

    def refreshed(self) -> tuple[Worktree, ...]:
        """git's list now, kept for the digest to check cookies against."""
        listed = self._source.listed()
        with self._lock:
            self._listed = listed
        return listed

    def known(self) -> tuple[Worktree, ...]:
        """The list the last page render saw, or nothing before the first render, which leaves a
        restarted panel's digest reading the launch directory until a page lists again."""
        with self._lock:
            return self._listed

    def reading(self, held: str | None, among: tuple[Worktree, ...]) -> tuple[Path, Backlog]:
        """The directory a request reads, and its backlog: the chosen worktree, else the launch.

        A panel started below a worktree's root reads the same place below the chosen worktree's
        root, since a knot project kept in a subdirectory is in that subdirectory in every
        checkout. Choosing the worktree the panel was started in reads the launch directory.
        """
        picked = chosen(held, among)
        if not picked:
            return self.launch, self._reader(self.launch)
        home = containing(self.launch, among)
        path = picked.path / self.launch.relative_to(home.path) if home else picked.path
        return path, self._reader(path)

    def marked(self, held: str | None, among: tuple[Worktree, ...]) -> Path | None:
        """The worktree the picker marks: the chosen one, else the one holding the launch."""
        picked = chosen(held, among) or containing(self.launch, among)
        return picked.path if picked else None

    def stamped(self, path: Path, digest: str) -> str:
        """A backlog's digest, told apart by the worktree it was read in.

        The launch directory's digest is the backlog's own, so a panel with one worktree answers
        exactly what it answered before. Any other worktree's is prefixed with a digest of its
        path, so switching moves the value every open tab compares against.
        """
        if path == self.launch:
            return digest
        where = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:8]
        return f"{where}.{digest}"

    def _reader(self, path: Path) -> Backlog:
        """The reader for one path, made on first use under the lock, so only once."""
        with self._lock:
            if path not in self._readers:
                self._readers[path] = self._opened(path)
            return self._readers[path]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest --no-cov tests/panel/test_worktree_choice.py -q`
Expected: all pass.

- [ ] **Step 6: Run the task's full verification**

Run: `uv run pytest && uv run ruff check src tests && uv run black --check src tests && uv run pylint src tests`
Expected: the suite passes at 100 percent coverage, and the linters are clean.

- [ ] **Step 7: Commit**
```bash
git add src/knotview/panel/worktree_choice.py src/knotview/panel/worktrees.py tests/panel/test_worktree_choice.py
dev-gate git commit -m "feat(panel): choose a worktree by cookie and keep one reader per worktree (kno-01m4mtc60xh9)"
```

---

### Task 3: Read the chosen worktree on every page

**Implements:** R4, R5, R6, R7, R9, R10, R12, R14, R16, AC-1 to AC-11, AC-12 (panel level),
AC-14, AC-15 (panel level), AC-17, AC-18, AC-21, AC-22 (panel level)
**Depends on:** Task 2   **Parallel with:** none

**Files:**
- Modify: `src/knotview/panel/app.py` (`Pages.__init__`, `_rendered`, `tags`,
  `unreadable`, every page handler, `_documents_of`, `_owner_of`, `_parent_of`, `digest`, `ROUTES`,
  `panel`; new `_backlog`, `_carried`, `worktree`, `_way_back`, `_here`)
- Create: `src/knotview/panel/templates/_worktrees.html`. A partial, because two frames include it.
- Modify: `src/knotview/panel/templates/layout.html`, `bare.html`
- Modify: `src/knotview/panel/static/follow.js`, `src/knotview/panel/static/panel.css`
- Test: `tests/panel/test_worktrees.py` (new), `tests/panel/test_routes.py`, `tests/panel/test_live.py`,
  `tests/panel/test_tags.py`, `tests/panel/test_overview_links.py`

**Interfaces:**
- Consumes: `Backlogs`, `Alone`, `WorktreeSource` (Task 2); `named`, `encoded`, `cookie_name`
  (Task 2); `Worktree` (Task 1).
- Produces:
  - `panel(backlog: Backlog, *, worktrees: WorktreeSource | None = None, opened: Callable[[Path], Backlog] | None = None) -> FastAPI`
  - Route `GET /worktree?path=&back=` and handler `Pages.worktree(request, path: str = "") -> Response`
  - Template context on every layout page: `worktrees` (a tuple, empty unless there are more than
    one), `reading` (a `Path` or `None`), and `carried` (a `str` or `None`).
  - Markup: `<nav class="worktrees">` with one `<a>` per worktree; `aria-current="true"` on the
    marked one; `data-digest` on `#live` when carried.

**Guardrails:** `/digest` must never call `Backlogs.refreshed`. Every route stays a GET. The
redirect target stays a path on this panel.

- [ ] **Step 1: Write the failing panel tests**

`tests/panel/test_worktrees.py`:
```python
"""Reading one of a repository's worktrees, chosen in the frame and kept in a cookie."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from knotview.panel.app import _given
from knotview.panel.worktree_choice import cookie_name, encoded
from knotview.values.worktree import Worktree
from tests.panel.declared import PARENT, DeclaredBacklog, RefusingBacklog, ticket

MAIN = Worktree(path=Path("/repo/knotview"), head="a" * 40, branch="refs/heads/main")
FEATURE = Worktree(path=Path("/repo/knotview-feature"), head="b" * 40, branch="refs/heads/feature")
REVIEW = Worktree(path=Path("/repo/knotview-review"), head="c1d2e3f4" + "0" * 32)
AWKWARD = Worktree(path=Path('/repo/my wt, x; "é"'), branch="refs/heads/odd")
FEATURE_ONLY = ticket("pro-01m2ffffffff", title="Only on the feature branch")
COOKIE = cookie_name(MAIN.path)


@dataclass
class DeclaredWorktrees:
    """A worktree source over a declared list, counting how often it is asked."""

    worktrees: tuple[Worktree, ...] = (MAIN, FEATURE)
    start: Path = MAIN.path
    calls: int = 0

    @property
    def launch(self) -> Path:
        """Where the panel was started."""
        return self.start

    def listed(self) -> tuple[Worktree, ...]:
        """The declared worktrees, counting the ask."""
        self.calls += 1
        return self.worktrees


@dataclass
class Opener:
    """Backlogs by path, noting every path a reader was made for."""

    held: dict[Path, object] = field(default_factory=dict)
    asked: list[Path] = field(default_factory=list)

    def __call__(self, path: Path) -> object:
        self.asked.append(path)
        return self.held[path]


def _panel(client, *, main=None, feature=None, source=None):
    """A browser over a panel with a main and a feature worktree, plus its source and opener."""
    opener = Opener(
        {
            FEATURE.path: feature
            or DeclaredBacklog(live_value=(FEATURE_ONLY,), digests=["f1"] * 3),
            REVIEW.path: DeclaredBacklog(),
            AWKWARD.path: DeclaredBacklog(live_value=(FEATURE_ONLY,)),
        }
    )
    source = source or DeclaredWorktrees()
    main = main or DeclaredBacklog(digests=["m1"] * 3)
    return client(main, worktrees=source, opened=opener), source, opener


def _marked(page: str) -> list[str]:
    """The labels of every picker entry marked as the one being read."""
    return re.findall(r'<a[^>]*aria-current="true"[^>]*>([^<]*)<', page)


def _choose(browser, worktree: Worktree, back: str = "/tree"):
    """Choose a worktree through the route, as the picker's link does."""
    return browser.get(
        "/worktree", params={"path": str(worktree.path), "back": back}, follow_redirects=False
    )


def test_the_frame_lists_each_worktree_by_name_and_directory_marking_the_one_read(client):
    browser, _, _ = _panel(client)

    page = browser.get("/tree").text

    assert "main · knotview" in page and "feature · knotview-feature" in page
    assert _marked(page) == ["main · knotview"]
    assert 'title="/repo/knotview-feature"' in page


def test_choosing_a_worktree_goes_back_to_the_page_and_every_page_then_reads_it(client):
    browser, _, _ = _panel(client)

    answer = _choose(browser, FEATURE)
    tree = browser.get("/tree").text
    tickets = browser.get("/tickets").text

    assert answer.status_code == 303 and answer.headers["location"] == "/tree"
    assert FEATURE_ONLY.title in tree and PARENT.title not in tree
    assert FEATURE_ONLY.title in tickets
    assert _marked(tickets) == ["feature · knotview-feature"]


def test_a_detached_worktree_is_offered_by_its_short_head(client):
    browser, _, _ = _panel(client, source=DeclaredWorktrees(worktrees=(MAIN, FEATURE, REVIEW)))

    assert "c1d2e3f · knotview-review" in browser.get("/tree").text


def test_a_cookie_naming_an_unlisted_directory_reads_the_launch_directory(client):
    browser, _, opener = _panel(client)

    page = browser.get("/tree", headers={"cookie": f"{COOKIE}={encoded(Path('/elsewhere'))}"})

    assert PARENT.title in page.text
    assert not opener.asked


def test_choosing_an_unlisted_path_clears_the_choice(client):
    browser, _, _ = _panel(client)
    _choose(browser, FEATURE)

    answer = browser.get("/worktree?path=/elsewhere&back=/", follow_redirects=False)

    assert answer.status_code == 303
    assert browser.cookies.get(COOKIE) is None
    assert PARENT.title in browser.get("/tree").text


def test_the_way_back_from_a_choice_must_be_a_path_on_this_panel(client):
    browser, _, _ = _panel(client)

    off = _choose(browser, FEATURE, back="https://elsewhere.example/")
    doubled = _choose(browser, FEATURE, back="//elsewhere.example")
    slanted = _choose(browser, FEATURE, back="/\\elsewhere.example")

    assert off.headers["location"] == doubled.headers["location"] == "/"
    assert slanted.headers["location"] == "/"


def test_the_default_factory_answers_the_one_backlog_for_any_path():
    backlog = DeclaredBacklog()

    assert _given(backlog, Path("/anywhere")) is backlog


def test_a_launch_below_a_worktree_root_reads_that_place_in_the_chosen_worktree(client):
    below = DeclaredWorktrees(start=MAIN.path / "sub")
    browser, _, opener = _panel(client, source=below)
    opener.held[FEATURE.path / "sub"] = DeclaredBacklog(live_value=(FEATURE_ONLY,))

    _choose(browser, FEATURE)

    assert FEATURE_ONLY.title in browser.get("/tree").text
    assert opener.asked == [FEATURE.path / "sub"]


def test_a_chosen_worktree_that_cannot_be_read_still_offers_the_picker(client):
    browser, _, _ = _panel(client, feature=RefusingBacklog())
    _choose(browser, FEATURE)

    page = browser.get("/")

    assert page.status_code == 503 and "no knot project here" in page.text
    assert "main · knotview" in page.text and 'back=/"' in page.text


def test_an_unreadable_launch_directory_still_offers_its_sibling_worktrees(client):
    browser, _, _ = _panel(client, main=RefusingBacklog())

    page = browser.get("/")

    assert page.status_code == 503 and "feature · knotview-feature" in page.text


def test_a_ticket_the_chosen_worktree_lacks_answers_not_found_with_the_picker(client):
    browser, _, _ = _panel(client)

    page = browser.get(
        "/worktree", params={"path": str(FEATURE.path), "back": f"/ticket/{PARENT.id}"}
    )

    assert page.status_code == 404
    assert _marked(page.text) == ["feature · knotview-feature"]


def test_a_launch_directory_inside_a_worktree_marks_that_worktree(client):
    inside, _, _ = _panel(client, source=DeclaredWorktrees(start=MAIN.path / "sub"))
    outside, _, _ = _panel(client, source=DeclaredWorktrees(start=Path("/elsewhere")))

    assert _marked(inside.get("/tree").text) == ["main · knotview"]
    assert _marked(outside.get("/tree").text) == []


def test_a_path_with_spaces_commas_semicolons_quotes_and_accents_can_be_chosen(client):
    browser, _, _ = _panel(client, source=DeclaredWorktrees(worktrees=(MAIN, AWKWARD)))

    _choose(browser, AWKWARD)

    assert FEATURE_ONLY.title in browser.get("/tree").text


def test_a_switch_moves_the_digest_away_from_the_one_the_page_carries(client):
    browser, _, _ = _panel(client)
    carried = re.search(r'data-digest="([^"]+)"', browser.get("/tree").text).group(1)

    _choose(browser, FEATURE)
    answer = browser.get("/digest").text

    assert carried == "m1"
    assert answer != carried and answer.endswith(".f1")


def test_the_digest_never_asks_git(client):
    browser, source, _ = _panel(client)
    browser.get("/tree")
    asked = source.calls

    browser.get("/digest")
    browser.get("/digest")

    assert source.calls == asked


def test_a_restarted_panel_answers_the_launch_digest_before_any_page_lists_worktrees(client):
    browser, source, opener = _panel(client)

    answer = browser.get("/digest", headers={"cookie": f"{COOKIE}={encoded(FEATURE.path)}"})

    assert answer.text == "m1"
    assert source.calls == 0 and not opener.asked


def test_a_removed_worktree_falls_back_to_the_launch_directory_and_leaves_the_picker(client):
    source = DeclaredWorktrees(worktrees=(MAIN, FEATURE, REVIEW))
    browser, _, _ = _panel(client, source=source)
    _choose(browser, FEATURE)

    source.worktrees = (MAIN, REVIEW)
    page = browser.get("/tree").text

    assert PARENT.title in page and "knotview-feature" not in page
    assert _marked(page) == ["main · knotview"]


def test_one_worktree_shows_no_picker(client):
    alone, _, _ = _panel(client, source=DeclaredWorktrees(worktrees=(MAIN,)))

    assert 'class="worktrees"' not in alone.get("/tree").text
    assert 'class="worktrees"' not in client(DeclaredBacklog()).get("/tree").text


def test_a_page_whose_digest_is_refused_renders_without_carrying_one(client):
    browser = client(DeclaredBacklog())

    first = browser.get("/tree").text
    second = browser.get("/tree").text

    assert 'data-digest="d1"' in first
    assert "data-digest" not in second and PARENT.title in second
```

In `tests/panel/test_routes.py`, add `"/worktree"` to `PATHS` and change the route count:
```python
PATHS = {
    "/static",
    "/",
    "/tickets",
    "/tree",
    "/queue/{which}",
    "/ticket/{identifier}",
    "/document/{identifier}",
    "/digest",
    "/tags",
    "/worktree",
}
```
```python
    assert len(routes) == 9
```

In `tests/panel/test_overview_links.py`, the filter test renders two pages on one backlog, and only
the first is carried a digest (the default sequence is `["d1"]`). The digest is not what the test
is about, so strip it as the tag bar's way back already is:
```python
def test_a_filter_in_the_overviews_url_changes_nothing(browser):
    """Apart from the tag bar's way back, which returns the reader to the URL they were on, and the
    digest a page carries, which is the backlog's and not the URL's."""
    back = re.compile(r'name="back" value="[^"]*"| data-digest="[^"]*"')

    assert back.sub("", browser.get(FILTERED).text) == back.sub("", browser.get("/").text)
```

In `tests/panel/test_tags.py`, extend `test_the_way_back_must_be_a_path_on_this_panel` with the
backslash case:
```python
    slanted = browser.get("/tags?add=p0&back=/%5Celsewhere.example", follow_redirects=False)
```
and add `slanted.headers["location"]` to its final equality chain.

Append to `tests/panel/test_live.py`:
```python
def test_the_poll_starts_from_the_digest_the_page_was_rendered_under():
    """Taking the first answer as the baseline let a tab rendered over one worktree adopt
    another's digest when a switch landed before its first poll, and never reload."""
    assert 'var known = badge.getAttribute("data-digest");' in FOLLOW
    assert "var known = null;" not in FOLLOW
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest --no-cov tests/panel/test_worktrees.py tests/panel/test_routes.py tests/panel/test_live.py -q`
Expected: failures with `TypeError: panel() got an unexpected keyword argument 'worktrees'`, the
route-table assertions failing, and the `follow.js` assertion failing.

- [ ] **Step 3: Wire `Pages` and `panel()` in `app.py`**

Add the imports:
```python
from collections.abc import Callable
from functools import partial

from knotview.panel.worktree_choice import encoded, named
from knotview.panel.worktrees import Alone, Backlogs, WorktreeSource
```

Replace `Pages.__init__` and `_rendered`, and add `_backlog` and `_carried` beneath them:
```python
    def __init__(self, backlogs: Backlogs, *, templates: Jinja2Templates) -> None:
        self.backlogs = backlogs
        self.templates = templates

    def _backlog(self, request: Request) -> Backlog:
        """The backlog this request reads, settled once per request with what the frame needs.

        The listing, the choice and the digest the page will carry are fixed on first use, so a
        page lists worktrees once however many reads it makes. The digest is read before any data:
        a write landing between the two then leaves a page newer than its digest, which costs one
        reload, rather than a page older than its digest, which would never reload.
        """
        held = getattr(request.state, "backlog", None)
        if held is not None:
            return held
        listed = self.backlogs.refreshed()
        cookie = request.cookies.get(self.backlogs.cookie)
        path, backlog = self.backlogs.reading(cookie, listed)
        request.state.worktrees = listed if len(listed) > 1 else ()
        request.state.reading = self.backlogs.marked(cookie, listed)
        request.state.carried = self._carried(path, backlog)
        request.state.backlog = backlog
        return backlog

    def _carried(self, path: Path, backlog: Backlog) -> str | None:
        """The digest a page carries for its poll to start from, or nothing if it cannot be read.

        Nothing rather than a refusal: the poll then takes its first answer as the baseline, as it
        did before pages carried one, and a page whose data can be read is still worth showing.
        """
        try:
            return self.backlogs.stamped(path, backlog.digest())
        except UnreadableBacklog:
            return None

    def _rendered(
        self, request: Request, template: str, *, status: int = 200, **context: object
    ) -> HTMLResponse:
        """One page, with what every page needs already in it: the project, the reader's tags,
        the worktrees to choose from and the digest the page was rendered under."""
        backlog = self._backlog(request)
        project = backlog.project()
        known = sorted({tag for one in backlog.live() for tag in one.tags})
        return self.templates.TemplateResponse(
            request=request,
            name=template,
            context={
                "project": project,
                "orders": ORDERS,
                "any": ANY,
                "tags": _tags(request),
                "known_tags": known,
                "here": _here(request),
                "worktrees": request.state.worktrees,
                "reading": request.state.reading,
                "carried": request.state.carried,
                **context,
            },
            status_code=status,
        )
```

Replace the redirect check inside `tags` with the shared helper:
```python
        answer = RedirectResponse(_way_back(request), status_code=303)
```
(and delete the three lines that computed `back` there).

Add the `worktree` handler after `tags`:
```python
    def worktree(self, request: Request, path: str = "") -> Response:
        """Choose the worktree every page reads, and go back to the page the reader was on.

        A GET like /tags, since it changes nothing but a cookie in the reader's browser. Only a
        worktree git lists right now can be chosen; anything else clears the choice, so the panel
        reads the directory it was started in.
        """
        picked = named(path, self.backlogs.refreshed())
        answer = RedirectResponse(_way_back(request), status_code=303)
        if picked:
            answer.set_cookie(
                self.backlogs.cookie, encoded(picked.path), samesite="strict", httponly=True
            )
        else:
            answer.delete_cookie(self.backlogs.cookie)
        return answer
```

Replace the `unreadable` context so the bare frame can offer the picker:
```python
        return self.templates.TemplateResponse(
            request=request,
            name="unreadable.html",
            context={
                "refusal": refusal,
                "worktrees": getattr(request.state, "worktrees", ()),
                "reading": getattr(request.state, "reading", None),
                "here": _here(request),
            },
            status_code=503,
        )
```

In every page handler, replace `self.backlog` with a local read once at the top:
- `overview`: `seen = Snapshot.read(self._backlog(request))`
- `tickets`: start with `backlog = self._backlog(request)`, then use `backlog.project()`,
  `backlog.live()`, `backlog.closed()` and `backlog.ticket(one.id)`.
- `tree`: `tree=Tree.over(self._narrowed(request, self._backlog(request).live()))`
- `queue`: start with `backlog = self._backlog(request)`, then
  `queues = {"ready": backlog.ready, "blocked": backlog.blocked}`.
- `ticket`: start with `backlog = self._backlog(request)`, then `ticket = backlog.ticket(identifier)`,
  `project = backlog.project()`, `parent = self._parent_of(backlog, ticket)`,
  `dependencies=backlog.dependencies(ticket.id)` and
  `documents=project.ordered(self._documents_of(backlog, ticket))`.
- `document`: start with `backlog = self._backlog(request)`, then
  `document = backlog.document(identifier)`, `project = backlog.project()` and
  `owner, siblings = self._owner_of(backlog, document)`.

Replace the three helpers so they take the backlog:
```python
    def _documents_of(self, backlog: Backlog, ticket: Ticket) -> tuple[Document, ...]:
        """A ticket's documents with their times, or as `show` stated them if knot will not list.

        Wider than `_parent_of`, which catches only a missing ticket: `show` has already read this
        ticket, so any refusal left is about its documents, and the times they would add are not
        worth a page that no longer renders.
        """
        try:
            return backlog.documents(ticket.id)
        except UnreadableBacklog:
            return ticket.documents

    def _owner_of(
        self, backlog: Backlog, document: Document
    ) -> tuple[Ticket | None, tuple[Document, ...]]:
        """The ticket a document belongs to and every document it owns, or nothing of either."""
        try:
            return backlog.ticket(document.ticket), backlog.documents(document.ticket)
        except MissingTicket:
            return None, ()

    def _parent_of(self, backlog: Backlog, ticket: Ticket) -> Ticket | None:
        """The ticket this one is filed under, read in full, or nothing if it names none.

        Read in full because the parent's children are what the page shows as siblings, and only
        a full read carries them. A parent that no longer exists is nothing rather than a refusal:
        the child is still worth reading, and the tree page already says it is a stray.
        """
        if not ticket.parent:
            return None
        try:
            return backlog.ticket(ticket.parent)
        except MissingTicket:
            return None
```

Replace `digest`:
```python
    def digest(self, request: Request) -> str:
        """What the chosen worktree's backlog looks like right now, as one short value to compare.

        Checked against the listing the last page render saw, never a fresh one: every open tab
        asks this about once a second, and git is not asked at that rate.
        """
        path, backlog = self.backlogs.reading(
            request.cookies.get(self.backlogs.cookie), self.backlogs.known()
        )
        return self.backlogs.stamped(path, backlog.digest())
```

Add the route:
```python
    ("/tags", "tags", None),
    ("/worktree", "worktree", None),
```

Replace `panel`'s signature and the `Pages` construction:
```python
def panel(
    backlog: Backlog,
    *,
    worktrees: WorktreeSource | None = None,
    opened: Callable[[Path], Backlog] | None = None,
) -> FastAPI:
    """The panel over one backlog, or over each worktree of the repository it belongs to.

    Built around an injected backlog rather than reaching for knot itself, which is what lets every
    page be tested against a backlog declared in a test while the real one drives a real project.
    The worktree source and the factory are optional: without them there is one worktree, this
    backlog, and the panel is exactly what it was before it knew about worktrees. This assembles;
    Pages renders.
    """
```
```python
    backlogs = Backlogs(
        launch=backlog,
        source=worktrees or Alone(Path.cwd()),
        opened=opened or partial(_given, backlog),
    )
    pages = Pages(backlogs, templates=templates)
```

Add the two module helpers near `_tags`:
```python
def _given(backlog: Backlog, _path: Path) -> Backlog:
    """The one backlog whatever path is asked for: the factory for a panel given no other."""
    return backlog


def _here(request: Request) -> str:
    """The path and query of this request, which every choice returns to."""
    return request.url.path + (f"?{request.url.query}" if request.url.query else "")


def _way_back(request: Request) -> str:
    """Where a choice returns to: a path on this panel, never an address elsewhere.

    A link from another site can carry any back value, and following it blindly would let this
    panel send a reader anywhere.
    """
    back = request.query_params.get("back") or "/"
    if not back.startswith("/") or back.startswith("//") or "\\" in back:
        # A browser reads a backslash after the first slash as a second slash, which makes
        # "/\\elsewhere" an address on another host.
        return "/"
    return back
```

Update the `Pages` class docstring's first paragraph so it no longer says "over one backlog":
```python
    """Every page the panel serves, each over the backlog its request reads.

    A class rather than a set of closures so that which backlogs the pages read from is a named
    attribute, and so that assembling the app (mounting the static files, registering the
    exception handler, writing out the route table) is separate from rendering a page.
```

- [ ] **Step 4: Add the picker and the carried digest to the templates**

`src/knotview/panel/templates/_worktrees.html`:
```html
{# The worktrees this panel can read, shown only when there is more than one to choose from.
Each is a link, a GET like every other: choosing changes a cookie in this browser and nothing
else. The full path is the title, since two entries can share a name or a directory. #}
{% if worktrees %}
<nav class="worktrees" aria-label="worktrees">
  {% for one in worktrees %}
  <a
    href="/worktree?path={{ one.path | string | urlencode }}&back={{ here | urlencode }}"
    title="{{ one.path }}"
    {% if one.path == reading %}aria-current="true"{% endif %}
    >{{ one.label }}</a
  >
  {% endfor %}
</nav>
{% endif %}
```

In `layout.html`, add the include right after the closing `</nav>` of the main navigation:
```html
      </nav>
      {% include "_worktrees.html" %}
```
and replace the live badge line with:
```html
      <span id="live" class="live" title="following the backlog"{% if carried %} data-digest="{{ carried }}"{% endif %}>live</span>
```

In `bare.html`, replace the header line with:
```html
    <header class="bar"><span class="brand">knotview</span>{% include "_worktrees.html" %}</header>
```

Append to `panel.css`, after the `.bar .addtag input[type="text"]` rule:
```css
.bar .worktrees {
  display: inline-flex;
  align-items: center;
  gap: 0.6em;
  margin-right: 0.8em;
  font-size: 0.85em;
}
.bar .worktrees a[aria-current="true"] {
  color: var(--ink);
  font-weight: 600;
  text-decoration: none;
}
```

- [ ] **Step 5: Take the poll's baseline from the page**

In `follow.js`, replace `var known = null;` with:
```javascript
  // The digest the page was rendered under, when the server could read one. Starting from it
  // rather than from the first answer means a change that lands before the first answer, such as
  // a worktree switched in another tab, still reloads this page. Without it, the first answer is
  // the baseline, as before.
  var known = badge.getAttribute("data-digest");
```
and replace the two comment lines above the first `if` in `ask` with:
```javascript
    // A page that carries no digest asks once even while hidden: the first answer records what it
    // was rendered from, so a tab opened in the background still reloads when shown after a change.
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest --no-cov tests/panel -q`
Expected: all pass. The only existing panel tests changed are `test_routes.py`,
`test_overview_links.py`, `test_tags.py` and `test_live.py`.

- [ ] **Step 7: Run the task's full verification**

Run: `uv run pytest && uv run ruff check src tests && uv run black --check src tests && uv run pylint src tests`
Expected: the suite passes at 100 percent line and branch coverage, and the linters are clean.

- [ ] **Step 8: Check it by hand in a browser**

Run, in this repository (which has `.tickets/`):
```bash
git worktree add ../knotview-wt-check -b jr/wt-check
uv run knotview --port 7791
```
Open `http://127.0.0.1:7791/tree` in two tabs.
Expected:
- The bar shows `jr/kno-01m4mtc60xh9-worktree-switching · knotview` (marked) and
  `jr/wt-check · knotview-wt-check`.
- Choosing the second entry returns to `/tree` showing that worktree's backlog. The other tab
  reloads by itself within about two seconds, and then also marks `jr/wt-check`.

Then stop the panel and clean up:
```bash
git worktree remove ../knotview-wt-check && git branch -D jr/wt-check
```
**Rollback:** the two clean-up commands above. They remove only the throwaway worktree and branch
made in this step.

- [ ] **Step 9: Commit**
```bash
git add src/knotview/panel/app.py src/knotview/panel/templates/_worktrees.html src/knotview/panel/templates/layout.html src/knotview/panel/templates/bare.html src/knotview/panel/static/follow.js src/knotview/panel/static/panel.css tests/panel/test_worktrees.py tests/panel/test_routes.py tests/panel/test_live.py tests/panel/test_tags.py tests/panel/test_overview_links.py
dev-gate git commit -m "feat(panel): read the worktree the reader chooses on every page (kno-01m4mtc60xh9)"
```

---

### Task 4: Serve every worktree from the command, and document it

**Implements:** R1 and R7 end to end (the command builds the real source and factory)
**Depends on:** Task 3   **Parallel with:** none

**Files:**
- Modify: `src/knotview/entry/console.py` (`main`)
- Modify: `tests/entry/test_console.py`
- Modify: `CLAUDE.md`, `README.md`

**Interfaces:**
- Consumes: `panel(backlog, *, worktrees, opened)` (Task 3); `GitWorktrees` (Task 1);
  `KnotCommand(*, repository, knot)`.
- Produces: nothing new.

**Guardrails:** no new command-line flag. The startup check still reads only the launch directory.

- [ ] **Step 1: Write the failing test**

In `tests/entry/test_console.py`, change the existing `panel` stand-in in
`test_main_serves_the_saved_project_on_its_saved_port` to accept options:
```python
    monkeypatch.setattr(console, "panel", lambda backlog, **_: backlog)
```
and add:
```python
def test_main_serves_every_worktree_of_the_repository_it_was_pointed_at(
    tmp_path: Path, monkeypatch
):
    built: list = []
    monkeypatch.setattr(console, "default_registry_path", lambda: tmp_path / "projects.toml")
    monkeypatch.setattr(console, "KnotCommand", _Backlog)
    monkeypatch.setattr(console, "panel", lambda backlog, **options: built.append(options))
    monkeypatch.setattr(console.uvicorn, "run", lambda app, **bound: None)

    assert console.main(["--repository", str(tmp_path), "--knot", "/opt/knot"]) == 0

    assert built[0]["worktrees"].launch == tmp_path.resolve()
    built[0]["opened"](tmp_path / "feature")
    assert _Backlog.built[-1] == (tmp_path / "feature", "/opt/knot")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest --no-cov tests/entry/test_console.py -q`
Expected: the new test fails with `KeyError: 'worktrees'`.

- [ ] **Step 3: Pass the source and factory**

In `console.py`, add the import:
```python
from knotview.reading.git_worktrees import GitWorktrees
```
and replace the `uvicorn.run(...)` line with:
```python
    # Every worktree of the repository, each read by its own knot command. The check above read
    # only the launch directory, which is the one a refusal there would be about.
    served = panel(
        backlog,
        worktrees=GitWorktrees(repository=repository),
        opened=lambda path: KnotCommand(repository=path, knot=asked.knot),
    )
    uvicorn.run(served, host=ADDRESS, port=port, log_level="warning")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest --no-cov tests/entry/test_console.py -q`
Expected: all pass.

- [ ] **Step 5: Document it**

In `CLAUDE.md` › Architecture, replace the sentence
"Every route is a GET, `READS` is disjoint from knot's write verbs, and only
`reading/knot_command.py` may start a process; tests assert all three." with:
```markdown
Every route is a GET, `READS` is disjoint from knot's write verbs, and only
`reading/knot_command.py` and `reading/git_worktrees.py` may start a process; tests assert all
three. git is only ever asked `worktree list --porcelain -z`.
```
and add this paragraph after the one about polling:
```markdown
A repository's worktrees each hold their own `.tickets/`. `GitWorktrees` lists them; the
`Backlogs` resolver in `panel/worktrees.py` keeps one `KnotCommand` per worktree under a lock and
picks one per request from the `knotview_worktree_<digest>` cookie, matched against git's list
(anything unlisted reads the launch directory). `Pages._backlog(request)` settles the listing, the
choice and the page's carried digest once per request; `/digest` checks the cookie against the last
page render's listing and never runs git.
```
In `CLAUDE.md` › Project Structure, replace the `reading/`, `panel/` and `values/` lines with:
```markdown
- `src/knotview/reading/` the `Backlog` port, its one implementation over `knot ... --json`, the
  envelope reader, and `GitWorktrees`, which lists the repository's worktrees
- `src/knotview/panel/` the FastAPI app (`Pages` and `panel()`), the selection, tree and overview
  values, the worktree resolver and cookie, the templates and the static files
- `src/knotview/values/` frozen dataclasses: Ticket, Project, Criterion, Reference, Worktree, and
  the two refusals
```
In `CLAUDE.md` › Architecture, in the paragraph about polling, replace "Each open page asks
`/digest` about once a second (not while hidden) for a digest of the ticket and document files'
names and modification times, and reloads itself when it changes." with:
```markdown
Each open page carries the digest it was rendered under and asks `/digest` about once a second
(not while hidden) for a digest of the ticket and document files' names and modification times,
reloading itself when the answer differs from what it carries.
```
and in the same paragraph replace "A hidden tab stops polling after its first answer and asks again
as soon as it is shown" with:
```markdown
A hidden tab does not poll and asks as soon as it is shown; only a page that carries no digest
asks once while hidden, to learn what it was rendered from
```
In `CLAUDE.md` › Key Files, add:
```markdown
- `src/knotview/reading/git_worktrees.py`: `GitWorktrees`, the pinned git argv, the porcelain parser.
- `src/knotview/panel/worktrees.py`: `Backlogs`, the per-worktree reader cache and the choice.
- `src/knotview/panel/worktree_choice.py`: the worktree cookie's name, encoding and matching.
```
In `CLAUDE.md` › Gotchas, add:
```markdown
- The worktree cookie is named per launch directory (`knotview_worktree_` plus a digest), because
  browsers share cookies across ports. Its value is a percent-encoded path, only used once it
  matches git's current list.
- A page reads its digest before its data and carries it as `data-digest` on `#live`; `follow.js`
  starts from it. A refused digest read renders the page without one. The launch directory's
  digest is the bare backlog digest; other worktrees' are prefixed with a digest of their path.
- Worktrees need git 2.36 or later (`-z`); an older or missing git silently means one worktree.
```
In `README.md`, after the paragraph about the tags bar (the one ending "the panel still writes
nothing."), add:
```markdown
When the repository has more than one git worktree, the bar also lists them, each by its branch
and directory. Choose one and every page reads that worktree's backlog, since each worktree holds
its own copy of `.tickets/`. The choice lives in a cookie in your browser, like the tags, and a
worktree git no longer lists falls back to the directory the panel was started in. Worktrees need
git 2.36 or later; without it the panel reads the one directory, as before.
```

- [ ] **Step 6: Run the task's full verification**

Run: `uv run pytest && uv run ruff check src tests && uv run black --check src tests && uv run pylint src tests`
Expected: the suite passes at 100 percent coverage, and the linters are clean.

- [ ] **Step 7: Commit**
```bash
git add src/knotview/entry/console.py tests/entry/test_console.py CLAUDE.md README.md
dev-gate git commit -m "feat(entry): serve every worktree of the repository the panel is pointed at (kno-01m4mtc60xh9)"
```
