# kno-01m2ebf3c8mx Test Coverage Implementation Plan

## Changes Since Last Cycle

- Task 3: the `integrity` body calls `self._read("check", verdict_read=True)` (finding 21).
- Task 5: the read-only guard is structural rather than a substring scan: only knot_command.py may
  import subprocess, and READS is disjoint from the write verbs (finding 20).
- Task 6: `DeclaredBacklog.digest` has one definition, the pop-then-raise one (finding 23).
- Task 8: the tree test asserts what `Tree.over` does today: a live child whose parent is not live
  vanishes; recorded as finding 19 for a follow-up (finding 22).
- Task 9: settled by probing: `knot init` needs no git repo, and a hand-written `:prefix` is
  honoured, so the fallback notes are gone.

**Goal:** `pytest` exits zero at 100 percent line and branch coverage, and the integrity path knot's
check actually reaches works end to end.

**Architecture:** The reading layer is tested through a fake `knot` script injected into
`KnotCommand`, driven by recorded envelopes under `tests/reading/envelopes/`. The panel is tested
through FastAPI's `TestClient` over a `DeclaredBacklog` that implements the `Backlog` protocol over
tuples. One scoped source change adds a check-aware envelope reader so `knot check`'s `ok: false`
health verdict is data rather than a refusal. One slow test drives the real binary for fidelity only.

**Tech Stack:** Python 3.12, pytest 8 with pytest-cov (branch, fail-under 100), FastAPI 0.141 /
starlette 1.6 / httpx 0.28 `TestClient`, knot 0.12.0 from the devenv tickets layer.

Spec: `docs/ai-assistant-ideation/kno-01m2ebf3c8mx-test-coverage-spec.md`. Run every command from
the repo root inside `devenv shell` (or prefix with `devenv shell --`). Commit after each task with
a conventional message and no trailers; the commit-msg hook rejects `Co-Authored-By`.

---

## File map

Create:
- `tests/reading/__init__.py`, `tests/reading/envelopes/__init__.py`
- `tests/reading/conftest.py` (the fake knot)
- `tests/reading/test_knot_envelope.py`, `tests/reading/test_knot_command.py`,
  `tests/reading/test_snapshot.py`, `tests/reading/test_real_knot.py`
- `tests/values/__init__.py`, `tests/values/test_ticket.py`, `tests/values/test_project.py`,
  `tests/values/test_unreadable_backlog.py`
- `tests/panel/__init__.py`, `tests/panel/declared.py`, `tests/panel/test_overview.py`,
  `tests/panel/test_tickets.py`, `tests/panel/test_tree.py`, `tests/panel/test_queue.py`,
  `tests/panel/test_ticket.py`, `tests/panel/test_unreadable.py`, `tests/panel/test_live.py`

Modify:
- `src/knotview/reading/knot_envelope.py:17-42` (`answered` split, new `verdict`) and the `_text`
  docstring at lines 112-119
- `src/knotview/reading/knot_command.py:86-103` (`integrity`), `126-131` (`_read` gains `verdict`),
  `176-194` (`_described`)

Already present (recorded, do not edit): `tests/reading/envelopes/*.json`.

---

### Task 1: Envelope loader and the fake knot

**Files:**
- Create: `tests/reading/__init__.py` (empty), `tests/reading/envelopes/__init__.py`,
  `tests/reading/conftest.py`

- [ ] **Step 1: The loader**

`tests/reading/envelopes/__init__.py`:
```python
"""Envelopes recorded from knot 0.12.0 on a probe project, one file per command shape.

Recorded rather than written, so the tests assert the shape knot actually emits. The probe held
a parent with two children (one archived), an orphan, a blank assignee and an absent one, a
blocker that is closed and one that is missing, a symmetric link, and one dangling dependency so
the check reports an issue. test_real_knot.py re-derives the same shapes from the binary.
"""

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def envelope(name: str) -> dict[str, Any]:
    """One recorded envelope, by the file's stem."""
    return json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
```

- [ ] **Step 2: The fake knot**

`tests/reading/conftest.py`:
```python
"""A knot that answers from the recorded envelopes, so the command can be driven to every branch.

Injected through KnotCommand's own constructor rather than put on PATH: no environment leaks
between tests, and the failure modes are chosen per command by the environment the fixture sets.
"""

import os
import stat
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from knotview.reading.knot_command import KnotCommand
from tests.reading.envelopes import HERE as ENVELOPES

SCRIPT = f'''#!{sys.executable}
import json, os, sys, time
from pathlib import Path

ENVELOPES = Path({str(ENVELOPES)!r})
verb = sys.argv[1] if len(sys.argv) > 1 else ""
mode = os.environ.get("KNOTVIEW_FAKE_MODE", "")
if mode == "junk":
    print("not json"); sys.exit(0)
if mode == "hang":
    time.sleep(5); sys.exit(0)


def say(name, code=0):
    sys.stdout.write((ENVELOPES / f"{{name}}.json").read_text(encoding="utf-8"))
    sys.exit(code)


if verb == "info":
    held = json.loads((ENVELOPES / "info.json").read_text(encoding="utf-8"))
    tickets = os.environ["KNOTVIEW_FAKE_TICKETS"]
    root = str(Path(tickets).parent)
    held["data"]["paths"] = {{
        "cwd": root, "project_root": root, "config_path": root + "/.knot.edn",
        "tickets_dir": ".tickets", "tickets_path": tickets, "archive_path": tickets + "/archive",
    }}
    print(json.dumps(held)); sys.exit(0)
if verb in ("list", "closed", "ready", "blocked"):
    say(verb)
if verb == "check":
    which = os.environ.get("KNOTVIEW_FAKE_CHECK", "clean")
    if which == "issues":
        say("check-issues")
    if which == "empty":
        print(json.dumps({{"schema_version": 1, "ok": False, "data": {{"issues": []}}}})); sys.exit(1)
    if which == "error":
        say("not-found", 1)
    say("check-clean")
if verb == "show":
    wanted = sys.argv[2]
    if wanted == "pro-01m2aaaaaaaa":
        say("show-parent")
    if wanted == "pro-01m2bbbbbbbb":
        say("show-child")
    if wanted == "list":
        say("list")
    say("not-found", 1)
sys.stderr.write(f"fake knot: unknown verb {{verb}}\\n"); sys.exit(2)
'''


@pytest.fixture
def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., KnotCommand]:
    """A KnotCommand over the fake, with the tickets directory it will digest already created."""
    script = tmp_path / "knot"
    script.write_text(SCRIPT, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    tickets = tmp_path / ".tickets"
    (tickets / "archive").mkdir(parents=True)
    monkeypatch.setenv("KNOTVIEW_FAKE_TICKETS", str(tickets))

    def build(*, mode: str = "", check: str = "clean", patience: int = 1) -> KnotCommand:
        monkeypatch.setenv("KNOTVIEW_FAKE_MODE", mode)
        monkeypatch.setenv("KNOTVIEW_FAKE_CHECK", check)
        return KnotCommand(repository=tmp_path, knot=str(script), patience=patience)

    return build
```

`patience` is an int of seconds because `KnotCommand` types it as `int`; the hang test uses 1.

- [ ] **Step 3: Smoke it**

Run: `devenv shell -- pytest tests/reading -q --no-cov`
Expected: "no tests ran" and no import error.

- [ ] **Step 4: Commit**

`git add tests/reading && git commit -m "test(reading): envelope loader and fake knot fixture"`

---

### Task 2: `verdict`, the check-aware envelope reader

**Files:**
- Modify: `src/knotview/reading/knot_envelope.py:17-42`
- Test: `tests/reading/test_knot_envelope.py`

- [ ] **Step 1: Failing tests**

`tests/reading/test_knot_envelope.py` (start of the file; later tasks append):
```python
"""Reading knot's own answer shape into this panel's values, from envelopes knot actually emitted."""

import pytest

from knotview.reading.knot_envelope import (
    answered,
    project_from,
    ticket_from,
    tickets_from,
    verdict,
)
from knotview.values.unreadable_backlog import UnreadableBacklog
from tests.reading.envelopes import envelope


def test_a_clean_check_is_data_with_no_issues():
    assert verdict(envelope("check-clean"), attempting="knot check")["issues"] == []


def test_a_check_with_issues_is_data_even_though_knot_says_not_ok():
    """knot's health verdict is ok:false co-emitted with data, which is the one documented
    carve-out from the envelope rule."""
    stated = envelope("check-issues")
    assert stated["ok"] is False

    issues = verdict(stated, attempting="knot check")["issues"]

    assert issues[0]["code"] == "unknown_id"


def test_a_refused_check_is_still_a_refusal():
    with pytest.raises(UnreadableBacklog, match="no ticket matching"):
        verdict(envelope("not-found"), attempting="knot check")


def test_not_ok_with_no_issues_key_is_a_failed_scan_not_a_clean_one():
    with pytest.raises(UnreadableBacklog, match="was refused"):
        verdict({"schema_version": 1, "ok": False, "data": {}}, attempting="knot check")


def test_not_ok_with_an_empty_issues_list_is_a_failed_scan_not_a_clean_one():
    with pytest.raises(UnreadableBacklog, match="was refused"):
        verdict({"schema_version": 1, "ok": False, "data": {"issues": []}}, attempting="knot check")


def test_the_verdict_still_checks_the_envelope_version():
    with pytest.raises(UnreadableBacklog, match="version 2"):
        verdict({"schema_version": 2, "ok": True, "data": {"issues": []}}, attempting="knot check")


def test_the_verdict_refuses_something_that_is_not_an_envelope():
    with pytest.raises(UnreadableBacklog, match="rather than an envelope"):
        verdict(["issues"], attempting="knot check")
```

- [ ] **Step 2: Run to see them fail**

Run: `devenv shell -- pytest tests/reading/test_knot_envelope.py -q --no-cov`
Expected: ImportError, `verdict` is not defined.

- [ ] **Step 3: Implement**

Replace `answered` in `src/knotview/reading/knot_envelope.py` with three functions:
```python
def answered(payload: dict[str, Any], *, attempting: str) -> Any:
    """The data out of one knot envelope, refusing an envelope that says it failed.

    The refusal carries knot's own message where it gave one, because knot already says the useful
    thing: which id was not found, which project is missing, which value was not allowed.
    """
    _versioned(payload, attempting=attempting)
    if not payload.get("ok"):
        raise _refused(payload, attempting=attempting)
    return payload.get("data")


def verdict(payload: dict[str, Any], *, attempting: str) -> Any:
    """The data out of knot's check, whose ok is a health verdict rather than a success flag.

    knot documents one carve-out from the envelope rule: check emits ok:false together with data
    whenever the project has issues, because ok answers "is the project healthy" there. So a
    not-ok check that carries a non-empty issues list is an answer, and the issues are what the
    reader came for. A not-ok check with no issues is a scan that failed, and stays a refusal:
    reading it as a clean project would hide exactly the failure the check exists to report.
    """
    _versioned(payload, attempting=attempting)
    if payload.get("ok"):
        return payload.get("data")
    stated = payload.get("data")
    if isinstance(stated, dict) and isinstance(stated.get("issues"), list) and stated["issues"]:
        return stated
    raise _refused(payload, attempting=attempting)


def _versioned(payload: Any, *, attempting: str) -> None:
    """Refuse anything that is not an envelope of the version this panel was written against."""
    if not isinstance(payload, dict):
        raise UnreadableBacklog(
            f"{attempting} answered with {type(payload).__name__} rather than an envelope",
            advice="check the knot version against the one this panel was written for",
        )
    if payload.get("schema_version") != SCHEMA:
        raise UnreadableBacklog(
            f"{attempting} answered with envelope version {payload.get('schema_version')!r} "
            f"rather than {SCHEMA}",
            advice="check whether knot's answer shape moved, and update this panel deliberately",
        )


def _refused(payload: dict[str, Any], *, attempting: str) -> UnreadableBacklog:
    """The refusal for a not-ok envelope, carrying knot's message where it gave one."""
    stated = payload.get("error") or {}
    said = stated.get("message") if isinstance(stated, dict) else None
    return UnreadableBacklog(
        f"{attempting} was refused: {said or 'knot gave no reason'}",
        advice="run the same knot command in that directory to see it in full",
    )
```

- [ ] **Step 4: Run to see them pass**

Run: `devenv shell -- pytest tests/reading/test_knot_envelope.py -q --no-cov`
Expected: 7 passed.

- [ ] **Step 5: Commit**

`git commit -am "fix(reading): read knot check's health verdict as data" && git add tests && git commit -m "test(reading): verdict over recorded check envelopes"` (two commits: source, then tests, or one `fix(reading)` commit holding both; either is fine).

---

### Task 3: `integrity` through the verdict, and issue lines from `ids`

**Files:**
- Modify: `src/knotview/reading/knot_command.py:86-103, 126-131, 176-194`
- Modify: `src/knotview/reading/knot_envelope.py` `_text` docstring
- Test: `tests/reading/test_knot_command.py`

- [ ] **Step 1: Failing tests**

`tests/reading/test_knot_command.py` (start; later tasks append):
```python
"""The backlog read by running knot, driven through a fake knot to every branch the real one has."""

import json
from pathlib import Path

import pytest

from knotview.reading.knot_command import READS, KnotCommand, _described
from knotview.values.unreadable_backlog import UnreadableBacklog
from tests.reading.envelopes import envelope


def test_a_clean_check_reports_no_issues(fake):
    assert fake(check="clean").integrity() == ()


def test_a_check_with_issues_reports_each_as_a_line_naming_the_ticket_and_the_code(fake):
    """This is the path knot's ok:false verdict used to close: the overview refused to render."""
    (line,) = fake(check="issues").integrity()

    assert line.startswith("pro-01m2bbbbbbbb unknown_id: unknown id")


def test_a_failed_scan_with_no_issues_is_refused_rather_than_read_as_clean(fake):
    with pytest.raises(UnreadableBacklog, match="was refused"):
        fake(check="empty").integrity()


def test_a_refused_check_is_refused(fake):
    with pytest.raises(UnreadableBacklog, match="no ticket matching"):
        fake(check="error").integrity()


def test_an_issue_line_carries_every_id_the_code_the_message_and_the_path():
    line = _described(
        {"ids": ["a", "b"], "code": "terminal_outside_archive", "message": "misplaced", "path": "/p"}
    )

    assert line == "a b terminal_outside_archive: misplaced (/p)"


def test_an_issue_that_is_only_text_passes_through():
    assert _described("a plain line") == "a plain line"


def test_an_issue_shaped_unexpectedly_is_shown_as_it_was_given():
    assert _described({"surprise": 1}) == json.dumps({"surprise": 1})
    assert _described(42) == "42"
```

- [ ] **Step 2: Run to see them fail**

Run: `devenv shell -- pytest tests/reading/test_knot_command.py -q --no-cov`
Expected: the issues test fails with UnreadableBacklog (the old path refuses ok:false); the
`_described` tests fail on the line shape.

- [ ] **Step 3: Implement**

In `knot_command.py`, import `verdict`:
```python
from knotview.reading.knot_envelope import (
    answered,
    project_from,
    ticket_from,
    tickets_from,
    verdict,
)
```
Replace the body of `integrity` after its docstring:
```python
        stated = self._read("check", verdict_read=True)
        issues = stated.get("issues") if isinstance(stated, dict) else None
        if not isinstance(issues, list):
            return ()
        return tuple(_described(issue) for issue in issues)
```
Change `_read`'s signature and its last line:
```python
    def _read(self, command: str, *arguments: str, verdict_read: bool = False) -> object:
        """One knot read, as data, refusing anything this panel was not written to run.

        The check is read through the verdict reader, because its ok is a health verdict rather
        than a success flag; every other read goes through the plain envelope rule.
        """
        ...
        wrap = verdict if verdict_read else answered
        return wrap(_data_in(answer, spoken), attempting=f"{self._knot} {command}")
```
(Name the keyword `verdict_read` so it does not shadow the imported function; `integrity` calls
`self._read("check", verdict_read=True)`.)

Replace `_described`:
```python
def _described(issue: object) -> str:
    """One integrity issue as a line, however knot chose to shape it.

    knot's check reports entries carrying ids (plural: an issue can span two tickets), a code, a
    message and sometimes a path. This states what it was given rather than insisting on that
    shape: a panel that refused to show an issue because the issue was shaped unexpectedly would
    be hiding exactly the thing worth showing.
    """
    if isinstance(issue, str):
        return issue
    if not isinstance(issue, dict):
        return str(issue)
    ids = issue.get("ids")
    where = " ".join(str(one) for one in ids) if isinstance(ids, list) else ""
    code = issue.get("code")
    message = issue.get("message")
    path = issue.get("path")
    if not (where or code or message):
        return json.dumps(issue)
    head = " ".join(part for part in (where, str(code) if code else "") if part)
    line = f"{head}: {message}" if head and message else (head or str(message))
    return f"{line} ({path})" if path else line
```

In `knot_envelope.py`, replace the `_text` docstring:
```python
    """One string, or nothing, with an empty string read as nothing.

    knot omits an unset assignee from both the listing and the read, and writes a blank one as an
    empty string in both, so absent and blank are the two shapes of "nobody". A panel that showed a
    blank string as a name assigned to nobody would be showing a difference that is not there.
    """
```

- [ ] **Step 4: Run to see them pass**

Run: `devenv shell -- pytest tests/reading -q --no-cov`
Expected: 14 passed.

- [ ] **Step 5: Commit**

`git add -A src tests && git commit -m "fix(reading): show knot check's issues instead of refusing the page"`

---

### Task 4: The rest of the envelope reader

**Files:**
- Test: `tests/reading/test_knot_envelope.py` (append)

- [ ] **Step 1: Tests**

```python
def test_answered_returns_the_data():
    assert answered(envelope("check-clean"), attempting="x")["scanned"]["live"] == 3


def test_answered_refuses_a_not_ok_envelope_with_knots_own_message():
    with pytest.raises(UnreadableBacklog, match="no ticket matching nope"):
        answered(envelope("not-found"), attempting="knot show")


def test_answered_refuses_a_not_ok_envelope_that_gives_no_reason():
    with pytest.raises(UnreadableBacklog, match="knot gave no reason"):
        answered({"schema_version": 1, "ok": False, "error": "text"}, attempting="knot show")


def test_answered_refuses_a_non_envelope_and_a_moved_version():
    with pytest.raises(UnreadableBacklog, match="rather than an envelope"):
        answered("nope", attempting="x")  # type: ignore[arg-type]
    with pytest.raises(UnreadableBacklog, match="version 0"):
        answered({"schema_version": 0}, attempting="x")


def test_the_project_is_read_from_info():
    project = project_from(envelope("info")["data"])

    assert (project.prefix, project.knot_version) == ("pro", "0.12.0")
    assert project.types == ("bug", "feature", "task", "epic", "chore")
    assert project.statuses == ("open", "in_progress", "closed")
    assert project.terminal_statuses == ("closed",)
    assert project.active_status == "in_progress"
    assert project.modes == ("afk", "hitl")
    assert project.priority_range == (0, 4)
    assert (project.live_count, project.archive_count) == (3, 1)
    assert project.tickets_path.endswith("/.tickets")


def test_a_project_with_no_name_is_called_unnamed():
    assert project_from(envelope("info")["data"]).name == "unnamed"


def test_a_project_stated_as_nothing_is_refused_and_a_half_stated_one_is_tolerated():
    with pytest.raises(UnreadableBacklog, match="no configuration"):
        project_from(None)
    assert project_from({}).types == ()


def test_a_listing_is_every_row_and_a_non_row_is_skipped():
    rows = envelope("list")["data"]

    read = tickets_from([*rows, "junk"], attempting="listing")

    assert [one.id for one in read] == [row["id"] for row in rows]


def test_a_listing_that_is_not_a_list_is_refused():
    with pytest.raises(UnreadableBacklog, match="rather than a list"):
        tickets_from({"id": "x"}, attempting="listing")


def test_a_ticket_with_no_id_is_refused():
    with pytest.raises(UnreadableBacklog, match="no id"):
        ticket_from({"title": "nameless"})


def test_absent_and_blank_assignees_are_both_nobody_and_a_name_is_kept():
    parent, child, orphan = tickets_from(envelope("list")["data"], attempting="listing")

    assert (parent.assignee, child.assignee, orphan.assignee) == (None, None, "someone")


def test_a_parent_is_kept_when_present_and_nothing_when_absent():
    parent, child, _ = tickets_from(envelope("list")["data"], attempting="listing")

    assert (parent.parent, child.parent) == (None, "pro-01m2aaaaaaaa")


def test_the_read_ticket_carries_criteria_tags_and_the_closed_child():
    parent = ticket_from(envelope("show-parent")["data"])

    assert [(c.title, c.done) for c in parent.acceptance] == [
        ("first thing", True),
        ("second thing", False),
    ]
    assert parent.tags == ("p0", "auth")
    assert [(c.id, c.status) for c in parent.children] == [
        ("pro-01m2bbbbbbbb", "in_progress"),
        ("pro-01m2cccccccc", "closed"),
    ]


def test_sections_keep_the_tickets_order_and_the_blank_heading_holds_the_preamble():
    parent = ticket_from(envelope("show-parent")["data"])

    assert list(parent.sections) == ["", "description", "design", "notes"]
    assert parent.sections[""] == "Text before any heading."
    assert parent.sections["design"] == "How it is built."


def test_an_empty_section_is_dropped():
    read = ticket_from({"id": "x", "sections": {"empty": "\n\n", "kept": "text\n"}})

    assert read.sections == {"kept": "text"}


def test_a_missing_blocker_arrives_with_a_blank_status_and_a_closed_one_with_its_title():
    child = ticket_from(envelope("show-child")["data"])

    assert [(b.id, b.status, b.title) for b in child.blockers] == [
        ("pro-01m2cccccccc", "closed", "The closed one"),
        ("pro-01m2zzzzzzzz", "", ""),
    ]
    assert [one.id for one in child.linked] == ["pro-01m2dddddddd"]


def test_a_closed_row_carries_its_closing_instant_and_untitled_reads_as_such():
    (closed,) = tickets_from(envelope("closed")["data"], attempting="closed")

    assert closed.closed == "2026-08-02T10:00:00.000000Z"
    assert ticket_from({"id": "x"}).title == "(untitled)"
```

- [ ] **Step 2: Run**

Run: `devenv shell -- pytest tests/reading/test_knot_envelope.py -q --no-cov`
Expected: all pass. If `project_from({})` raises on `priority_range`, that is the reader's own
`_mapping` returning `{}` and `int(span.get("min", 0))` succeeding, so it should not; if it does,
report it as a finding rather than changing the reader.

- [ ] **Step 3: Commit**

`git add tests && git commit -m "test(reading): the envelope reader over recorded shapes"`

---

### Task 5: The command over the fake, its failures, the digest and the guard

**Files:**
- Test: `tests/reading/test_knot_command.py` (append)

- [ ] **Step 1: Tests**

```python
def test_every_listing_read_answers_from_its_envelope(fake):
    command = fake()

    assert command.project().prefix == "pro"
    assert [one.id for one in command.live()] == [r["id"] for r in envelope("list")["data"]]
    assert [one.id for one in command.closed()] == ["pro-01m2cccccccc"]
    assert [one.id for one in command.ready()] == ["pro-01m2aaaaaaaa", "pro-01m2dddddddd"]
    assert [one.id for one in command.blocked()] == ["pro-01m2bbbbbbbb"]


def test_one_ticket_is_read_in_full_by_its_id(fake):
    child = fake().ticket("pro-01m2bbbbbbbb")

    assert child.title == "The child"
    assert child.sections == {"description": "The child does a thing."}


def test_an_unknown_id_refuses_with_knots_own_message(fake):
    with pytest.raises(UnreadableBacklog, match="no ticket matching nope"):
        fake().ticket("nope")


def test_a_show_that_answers_a_list_is_refused_as_not_a_ticket(fake):
    with pytest.raises(UnreadableBacklog, match="rather than a ticket"):
        fake().ticket("list")


def test_output_that_is_not_json_refuses_naming_the_command(fake):
    with pytest.raises(UnreadableBacklog, match="list --json printed nothing this panel can read"):
        fake(mode="junk").live()


def test_a_knot_that_hangs_refuses_after_the_patience(fake):
    with pytest.raises(UnreadableBacklog, match="did not answer within 1 seconds"):
        fake(mode="hang", patience=1).project()


def test_a_missing_binary_refuses_naming_it(tmp_path: Path):
    absent = KnotCommand(repository=tmp_path, knot=str(tmp_path / "absent"))

    with pytest.raises(UnreadableBacklog, match="absent is not on the path"):
        absent.project()


def test_a_verb_outside_the_reads_is_refused_before_anything_runs(fake):
    """Called on the private read on purpose: every public method passes a literal from READS,
    so nothing public can reach this guard. It exists for the next method somebody adds."""
    with pytest.raises(UnreadableBacklog, match="delete is not one of the reads"):
        fake()._read("delete")  # noqa: SLF001


def test_the_repository_is_named(fake, tmp_path: Path):
    assert fake().repository == tmp_path


def test_the_digest_is_absent_when_there_is_no_tickets_directory(fake, tmp_path: Path):
    (tmp_path / ".tickets" / "archive").rmdir()
    (tmp_path / ".tickets").rmdir()

    assert fake().digest() == "absent"


def test_the_digest_is_stable_and_moves_when_a_ticket_file_does(fake, tmp_path: Path):
    ticket = tmp_path / ".tickets" / "pro-01m2aaaaaaaa--the-parent.md"
    ticket.write_text("---\nid: pro-01m2aaaaaaaa\n---\n", encoding="utf-8")
    command = fake()
    before = command.digest()

    assert command.digest() == before
    import os
    os.utime(ticket, ns=(ticket.stat().st_atime_ns, ticket.stat().st_mtime_ns + 1_000_000))
    assert command.digest() != before


def test_the_digest_covers_the_archive(fake, tmp_path: Path):
    command = fake()
    before = command.digest()

    (tmp_path / ".tickets" / "archive" / "pro-01m2cccccccc--closed.md").write_text("x")

    assert command.digest() != before


WRITE_VERBS = (
    "create", "start", "status", "close", "reopen", "delete",
    "dep", "undep", "link", "unlink", "add-note", "edit", "update",
)


def test_the_reads_are_the_only_verbs_and_none_of_them_writes():
    assert set(READS).isdisjoint(WRITE_VERBS)


def test_only_the_command_module_reaches_outside_the_process():
    """The read-only guarantee is structural: knot is invoked in exactly one module, every verb it
    is handed comes from READS, and READS holds no write verb. So the guard is on who may run a
    process at all, not on which words appear in the package: "status" is also a field name."""
    source = Path(__import__("knotview").__file__).resolve().parent
    running = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*.py")
        if "subprocess" in path.read_text(encoding="utf-8")
    }
    assert running == {"reading/knot_command.py"}


def test_the_command_only_speaks_the_verb_it_was_given(fake):
    """_spoken is the one place argv is built, and it puts the READS verb first and --json last."""
    assert fake()._spoken("list", ())[1:] == ["list", "--json"]  # noqa: SLF001
    assert fake()._spoken("show", ("x",))[1:] == ["show", "x", "--json"]  # noqa: SLF001
```

Move `import os` to the top of the module.

- [ ] **Step 2: Run**

Run: `devenv shell -- pytest tests/reading -q --no-cov`
Expected: all pass; the hang test takes about one second.

- [ ] **Step 3: Commit**

`git add tests && git commit -m "test(reading): the command over a fake knot, its refusals, the digest and the read-only guard"`

---

### Task 6: Snapshot and the port

**Files:**
- Test: `tests/reading/test_snapshot.py`
- Create: `tests/panel/__init__.py` (empty), `tests/panel/declared.py`

- [ ] **Step 1: The declared backlog** (used by every panel test and by the snapshot test)

`tests/panel/declared.py`:
```python
"""A backlog declared in a test, so every page can be asserted without a process."""

from dataclasses import dataclass, field

from knotview.values.criterion import Criterion
from knotview.values.project import Project
from knotview.values.reference import Reference
from knotview.values.ticket import Ticket
from knotview.values.unreadable_backlog import UnreadableBacklog

PROJECT = Project(
    name="probe",
    prefix="pro",
    knot_version="0.12.0",
    types=("bug", "feature", "task", "epic", "chore"),
    statuses=("open", "in_progress", "closed"),
    active_status="in_progress",
    terminal_statuses=("closed",),
    modes=("afk", "hitl"),
    priority_range=(0, 4),
    tickets_path="/nowhere/.tickets",
    live_count=3,
    archive_count=1,
)


def ticket(identifier: str, **held: object) -> Ticket:
    """A ticket with sensible defaults, so a test names only what it is about."""
    given: dict = {
        "id": identifier,
        "title": f"Ticket {identifier}",
        "status": "open",
        "type": "task",
        "priority": 2,
        "created": "2026-09-01T10:00:00.000000Z",
        "updated": "2026-09-02T10:00:00.000000Z",
    }
    given.update(held)
    return Ticket(**given)


PARENT = ticket(
    "pro-01m2aaaaaaaa",
    title="The parent",
    type="epic",
    priority=1,
    tags=("p0", "auth"),
    acceptance=(Criterion(title="first thing", done=True), Criterion(title="second thing", done=False)),
    children=(Reference(id="pro-01m2bbbbbbbb", title="The child", status="in_progress"),),
    sections={"": "Text before any heading.", "description": "What for.", "notes": "A note."},
)
CHILD = ticket(
    "pro-01m2bbbbbbbb",
    title="The child",
    status="in_progress",
    mode="afk",
    parent="pro-01m2aaaaaaaa",
    updated="2026-09-04T10:00:00.000000Z",
    blockers=(
        Reference(id="pro-01m2cccccccc", title="The closed one", status="closed"),
        Reference(id="pro-01m2zzzzzzzz", title="", status=""),
    ),
    linked=(Reference(id="pro-01m2dddddddd", title="The orphan", status="open"),),
    external_refs=("https://example.test/1",),
)
ORPHAN = ticket(
    "pro-01m2dddddddd", title="The orphan", type="bug", priority=3, assignee="someone"
)
CLOSED = ticket(
    "pro-01m2cccccccc",
    title="The closed one",
    status="closed",
    type="chore",
    priority=4,
    parent="pro-01m2aaaaaaaa",
    closed="2026-08-02T10:00:00.000000Z",
)


@dataclass(kw_only=True)
class DeclaredBacklog:
    """A Backlog over tuples, counting how often the digest is asked for."""

    project_value: Project = PROJECT
    live_value: tuple[Ticket, ...] = (PARENT, CHILD, ORPHAN)
    closed_value: tuple[Ticket, ...] = (CLOSED,)
    ready_value: tuple[Ticket, ...] = (PARENT, ORPHAN)
    blocked_value: tuple[Ticket, ...] = (CHILD,)
    integrity_value: tuple[str, ...] = ()
    digests: list[str] = field(default_factory=lambda: ["d1"])
    digest_calls: int = 0

    def project(self) -> Project:
        return self.project_value

    def live(self) -> tuple[Ticket, ...]:
        return self.live_value

    def closed(self) -> tuple[Ticket, ...]:
        return self.closed_value

    def ready(self) -> tuple[Ticket, ...]:
        return self.ready_value

    def blocked(self) -> tuple[Ticket, ...]:
        return self.blocked_value

    def ticket(self, identifier: str) -> Ticket:
        for held in (*self.live_value, *self.closed_value):
            if held.id == identifier:
                return held
        raise UnreadableBacklog(
            f"knot show was refused: no ticket matching {identifier}",
            advice="check the id against knot list",
        )

    def integrity(self) -> tuple[str, ...]:
        return self.integrity_value

    def digest(self) -> str:
        self.digest_calls += 1
        if not self.digests:
            raise UnreadableBacklog("the tickets directory went away", advice="point it back")
        return self.digests.pop(0)


class RefusingBacklog:
    """A backlog that cannot be read at all, which is the wrong-directory case."""

    def _refuse(self, *_: object) -> None:
        raise UnreadableBacklog("no knot project here", advice="run knot init, or point elsewhere")

    project = live = closed = ready = blocked = ticket = integrity = digest = _refuse
```

Each digest call pops the next value and raises once the list is empty; the `/digest` test seeds
`["d1"]` and the live test seeds `["A", "A", "B"]`, so its fourth call is the unreadable event.

- [ ] **Step 2: Snapshot test**

`tests/reading/test_snapshot.py`:
```python
"""One read of a backlog, taken together."""

import pytest

from knotview.reading.backlog import Backlog
from knotview.reading.snapshot import Snapshot
from tests.panel.declared import CHILD, CLOSED, ORPHAN, PARENT, DeclaredBacklog


def test_a_snapshot_carries_every_part_of_one_read():
    backlog = DeclaredBacklog(integrity_value=("a line",))

    taken = Snapshot.read(backlog)

    assert taken.project is backlog.project_value
    assert taken.live == (PARENT, CHILD, ORPHAN)
    assert taken.closed == (CLOSED,)
    assert (taken.ready, taken.blocked) == ((PARENT, ORPHAN), (CHILD,))
    assert taken.integrity == ("a line",)


def test_the_declared_backlog_satisfies_the_port():
    assert isinstance(DeclaredBacklog(), Backlog)


@pytest.mark.parametrize(
    "name", ["project", "live", "closed", "ready", "blocked", "integrity", "digest"]
)
def test_the_port_itself_answers_nothing(name: str):
    """The protocol's bodies are refusals, not defaults, so a class that inherits one by mistake
    fails at the call rather than answering an empty backlog."""
    with pytest.raises(NotImplementedError):
        getattr(Backlog, name)(object())


def test_the_port_itself_answers_no_ticket_either():
    with pytest.raises(NotImplementedError):
        Backlog.ticket(object(), "x")
```

- [ ] **Step 3: Run and commit**

Run: `devenv shell -- pytest tests/reading/test_snapshot.py -q --no-cov`
Expected: 10 passed.
`git add tests && git commit -m "test(reading): the snapshot and the declared backlog"`

---

### Task 7: Value types

**Files:**
- Create: `tests/values/__init__.py`, `tests/values/test_ticket.py`, `tests/values/test_project.py`,
  `tests/values/test_unreadable_backlog.py`

- [ ] **Step 1: Tests**

`tests/values/test_ticket.py`:
```python
"""What a ticket derives from what it holds."""

from tests.panel.declared import CHILD, PARENT, ticket


def test_criteria_are_counted_and_the_unmet_ones_named():
    assert (PARENT.met, PARENT.criteria) == (1, 2)
    assert [one.title for one in PARENT.unmet] == ["second thing"]
    assert (CHILD.met, CHILD.criteria, CHILD.unmet) == (0, 0, ())


def test_only_blockers_that_are_not_closed_are_open_and_a_missing_one_counts_as_open():
    """A missing blocker arrives with no status. Counting it as open is the current behaviour and
    is asserted as such; showing it as missing is a follow-up."""
    assert [one.id for one in CHILD.open_blockers] == ["pro-01m2zzzzzzzz"]


def test_the_notes_are_named_and_kept_out_of_the_narrative():
    assert PARENT.notes == "A note."
    assert PARENT.narrative() == (("", "Text before any heading."), ("description", "What for."))
    assert ticket("x").notes is None
```

`tests/values/test_project.py`:
```python
"""What a project derives from its declared values."""

from tests.panel.declared import PROJECT


def test_open_statuses_are_the_declared_ones_that_are_not_terminal():
    assert PROJECT.open_statuses == ("open", "in_progress")


def test_priorities_run_the_declared_range_highest_first():
    assert PROJECT.priorities == (0, 1, 2, 3, 4)


def test_a_status_is_terminal_when_the_project_says_so():
    assert PROJECT.is_terminal("closed") and not PROJECT.is_terminal("open")
```

`tests/values/test_unreadable_backlog.py`:
```python
"""The refusal carries its advice as a field and in its message."""

from knotview.values.unreadable_backlog import UnreadableBacklog


def test_the_message_and_the_advice_are_both_kept_and_joined():
    refusal = UnreadableBacklog("could not read", advice="point it at a project")

    assert (refusal.message, refusal.advice) == ("could not read", "point it at a project")
    assert str(refusal) == "could not read. point it at a project"
```

- [ ] **Step 2: Run and commit**

Run: `devenv shell -- pytest tests/values -q --no-cov` — expected 7 passed.
`git add tests && git commit -m "test(values): derived properties of ticket, project and the refusal"`

---

### Task 8: The pages

**Files:**
- Create: `tests/panel/conftest.py`, `tests/panel/test_overview.py`, `tests/panel/test_tickets.py`,
  `tests/panel/test_tree.py`, `tests/panel/test_queue.py`, `tests/panel/test_ticket.py`,
  `tests/panel/test_unreadable.py`, `tests/panel/test_live.py`

- [ ] **Step 1: Client fixture**

`tests/panel/conftest.py`:
```python
"""A client over the panel, built per test so a backlog can be declared for it."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from knotview.panel.app import panel


@pytest.fixture
def client() -> Callable[..., TestClient]:
    def build(backlog, **options) -> TestClient:
        return TestClient(panel(backlog, **options))

    return build
```

- [ ] **Step 2: Overview**

`tests/panel/test_overview.py`:
```python
"""The first page: the backlog counted the ways a reader asks about it."""

from knotview.reading.knot_command import _described
from tests.panel.declared import DeclaredBacklog, ticket
from tests.reading.envelopes import envelope


def test_every_declared_type_is_counted_even_at_zero_with_a_link_to_its_filter(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a href="/tickets?type=feature"' in page
    assert page.count("num") >= 5
    assert "epic" in page and "chore" in page


def test_statuses_priorities_and_queues_are_counted(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a href="/tickets?status=in_progress"' in page
    assert '<a href="/tickets?priority=3"' in page
    assert '<a href="/queue/ready">ready</a>' in page
    assert "unassigned" in page
    assert '<a href="/tickets?closed=1">1</a>' in page


def test_the_live_total_is_the_sum_over_statuses(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a href="/tickets">live</a' in page and ">3</span>" in page


def test_parents_are_whatever_something_is_filed_under_and_closed_work_is_listed(client):
    page = client(DeclaredBacklog()).get("/").text

    assert "The parent" in page
    assert "The closed one" in page


def test_recently_closed_is_capped(client):
    many = tuple(ticket(f"pro-01m2{i:08d}", status="closed", title=f"Closed {i}") for i in range(10))
    page = client(DeclaredBacklog(closed_value=many)).get("/").text

    assert "Closed 7" in page and "Closed 8" not in page


def test_a_clean_project_shows_no_integrity_section(client):
    assert "integrity" not in client(DeclaredBacklog()).get("/").text


def test_integrity_issues_are_listed_as_knot_reported_them_at_200():
    """AC 3: the line comes from the recorded check through the real formatter."""
    lines = tuple(_described(one) for one in envelope("check-issues")["data"]["issues"])
    from fastapi.testclient import TestClient
    from knotview.panel.app import panel

    response = TestClient(panel(DeclaredBacklog(integrity_value=lines))).get("/")

    assert response.status_code == 200
    assert "pro-01m2bbbbbbbb unknown_id: unknown id" in response.text
```
(Use the `client` fixture in the last test too; the inline imports are shown only for clarity.)

- [ ] **Step 3: Tickets**

`tests/panel/test_tickets.py`:
```python
"""Every ticket the filters admit, in the order asked for, with every filter kept in the links."""

import pytest

from knotview.panel.selection import ANY, Selection
from tests.panel.declared import CHILD, ORPHAN, PARENT, PROJECT, DeclaredBacklog, ticket


def titles(page: str) -> list[str]:
    return [name for name in ("The parent", "The child", "The orphan", "The closed one") if name in page]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", ["The parent", "The child", "The orphan"]),
        ("type=bug", ["The orphan"]),
        ("status=in_progress", ["The child"]),
        ("priority=1", ["The parent"]),
        ("mode=afk", ["The child"]),
        ("assignee=someone", ["The orphan"]),
        ("tag=auth", ["The parent"]),
        ("q=orphan", ["The orphan"]),
        ("q=pro-01m2bbbb", ["The child"]),
        ("q=p0", ["The parent"]),
        ("type=nonsense", ["The parent", "The child", "The orphan"]),
        ("closed=1", ["The parent", "The child", "The orphan", "The closed one"]),
        ("closed=1&status=closed", ["The closed one"]),
    ],
)
def test_each_filter_narrows_and_an_undeclared_value_is_dropped(client, query, expected):
    page = client(DeclaredBacklog()).get(f"/tickets?{query}").text

    assert titles(page) == expected


def test_the_summary_line_counts_shown_of_held_and_the_clear_link_appears_only_when_filtering(client):
    plain = client(DeclaredBacklog()).get("/tickets").text
    narrowed = client(DeclaredBacklog()).get("/tickets?type=bug").text

    assert "3 of 3" in plain and "clear" not in plain
    assert "1 of 3" in narrowed and '<a class="clear" href="/tickets">clear</a>' in narrowed
    assert "type bug" in narrowed


def test_orders_priority_first_by_default_and_newest_first_by_update(client):
    by_priority = client(DeclaredBacklog()).get("/tickets").text
    by_update = client(DeclaredBacklog()).get("/tickets?order=updated").text

    assert by_priority.index("The parent") < by_priority.index("The child") < by_priority.index("The orphan")
    assert by_update.index("The child") < by_update.index("The parent")


def test_ties_break_on_id_and_title_order_ignores_case(client):
    a = ticket("pro-01m2zzzzzzzz", title="alpha")
    b = ticket("pro-01m2yyyyyyyy", title="Beta")
    backlog = DeclaredBacklog(live_value=(a, b))

    by_priority = client(backlog).get("/tickets").text
    by_title = client(backlog).get("/tickets?order=title").text
    by_created = client(backlog).get("/tickets?order=created").text
    by_id = client(backlog).get("/tickets?order=id").text

    assert by_priority.index("Beta") < by_priority.index("alpha")
    assert by_title.index("alpha") < by_title.index("Beta")
    assert by_created.index("Beta") < by_created.index("alpha")
    assert by_id.index("Beta") < by_id.index("alpha")


def test_a_selection_round_trips_through_its_query_string_and_omits_the_defaults():
    asked = Selection.asked(PROJECT, {"type": "bug", "order": "priority", "closed": "yes", "q": " x "})

    assert asked.query_string() == "type=bug&q=x&closed=1"
    assert asked.query_string(order="title") == "type=bug&q=x&order=title&closed=1"
    assert Selection().query_string() == ""
    assert Selection.asked(PROJECT, {"assignee": " "}).assignee == ANY


def test_the_applied_filters_are_named_for_the_summary():
    assert Selection(type="bug", query="x").applied() == (("type", "bug"), ("matching", "x"))
    assert Selection().filtering is False


def test_matching_and_ordering_as_values():
    narrowed = Selection(tag="auth")
    assert narrowed.matches(PARENT) and not narrowed.matches(CHILD)
    assert Selection(query="nothing").matches(ORPHAN) is False
    assert Selection(order="id").ordered((ORPHAN, PARENT))[0] is PARENT
```

- [ ] **Step 4: Tree**

`tests/panel/test_tree.py`:
```python
"""What is filed under what, with each parent's progress counted."""

from knotview.panel.tree import Tree
from tests.panel.declared import CHILD, ORPHAN, PARENT, DeclaredBacklog, ticket


def test_a_branch_shows_its_children_counted_and_the_parents_own_criteria(client):
    page = client(DeclaredBacklog()).get("/tree").text

    assert "children 0/1" in page
    assert "criteria 1/2" in page
    assert "filed under nothing" in page and "The orphan" in page


def test_a_complete_branch_that_is_still_open_says_so(client):
    done = ticket("pro-01m2bbbbbbbb", status="closed", parent="pro-01m2aaaaaaaa")
    page = client(DeclaredBacklog(live_value=(PARENT, done))).get("/tree").text

    assert "Every child is done and this is still open" in page
    assert "children 1/1" in page


def test_a_child_whose_parent_is_not_live_vanishes_from_the_tree():
    """Current behaviour, asserted rather than endorsed: a ticket naming a parent that is not in
    the live set is neither a branch child nor an orphan. Recorded as a finding for a follow-up
    that shows it under "filed under nothing"."""
    stray = ticket("pro-01m2eeeeeeee", parent="pro-01m2gone")

    shape = Tree.over((CHILD, ORPHAN, stray), terminal=("closed",))

    assert shape.branches == ()
    assert [one.id for one in shape.orphans] == ["pro-01m2dddddddd"]


def test_branches_and_children_are_ordered_by_priority_then_id():
    low = ticket("pro-01m2ffffffff", priority=4, title="Low parent")
    kid = ticket("pro-01m2gggggggg", priority=0, parent="pro-01m2ffffffff")
    kid2 = ticket("pro-01m2hhhhhhhh", priority=0, parent="pro-01m2aaaaaaaa")

    shape = Tree.over((low, kid, PARENT, CHILD, kid2), terminal=("closed",))

    assert [b.parent.id for b in shape.branches] == ["pro-01m2aaaaaaaa", "pro-01m2ffffffff"]
    assert [c.id for c in shape.branches[0].children] == ["pro-01m2hhhhhhhh", "pro-01m2bbbbbbbb"]
    assert shape.branches[0].complete is False and shape.branches[0].total == 2
```
Settled at plan review by reading `tree.py:81`: the orphan rule is `not ticket.parent`, so a
child of a non-live parent is dropped. Finding 19 records it; `tree.py` is outside this story's
source scope.

- [ ] **Step 5: Queue, ticket, unreadable**

`tests/panel/test_queue.py`:
```python
"""knot's own queues, and the page for a queue this panel does not have."""

from tests.panel.declared import DeclaredBacklog


def test_ready_and_blocked_list_their_tickets(client):
    ready = client(DeclaredBacklog()).get("/queue/ready").text
    blocked = client(DeclaredBacklog()).get("/queue/blocked").text

    assert "Every blocker closed" in ready and "The parent" in ready and "The child" not in ready
    assert "At least one blocker still open" in blocked and "The child" in blocked


def test_an_unknown_queue_is_a_page_that_says_so_at_200(client):
    response = client(DeclaredBacklog()).get("/queue/soon")

    assert response.status_code == 200
    assert "This panel has no a queue called soon." in response.text
```

`tests/panel/test_ticket.py`:
```python
"""One ticket in full."""

from knotview.panel.app import _humanise
from tests.panel.declared import CHILD, DeclaredBacklog, ticket


def test_the_header_carries_the_chips_the_instants_and_the_parent(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text

    assert "<h1>The child</h1>" in page
    assert 'href="/tickets?mode=afk"' in page
    assert "nobody" in page
    assert "created 2026-09-01 10:00 · updated 2026-09-04 10:00" in page
    assert '<a href="/ticket/pro-01m2aaaaaaaa">pro-01m2aaaaaaaa</a>' in page


def test_criteria_sections_tags_and_notes_are_rendered_in_the_tickets_own_order(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2aaaaaaaa").text

    assert "acceptance <span class=\"num\">1/2</span>" in page
    assert "✓" in page and "○" in page
    assert page.index("Text before any heading.") < page.index("What for.") < page.index("A note.")
    assert 'href="/tickets?tag=auth"' in page


def test_every_graph_direction_and_the_external_refs_are_listed(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text

    assert "blocked by" in page and "The closed one" in page
    assert "linked" in page and "The orphan" in page
    assert "https://example.test/1" in page
    parent = client(DeclaredBacklog()).get("/ticket/pro-01m2aaaaaaaa").text
    assert "children" in parent


def test_a_closed_ticket_shows_when_it_closed_and_an_assignee_is_a_link(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2cccccccc").text
    assert "closed 2026-08-02 10:00" in page
    orphan = client(DeclaredBacklog()).get("/ticket/pro-01m2dddddddd").text
    assert 'href="/tickets?assignee=someone"' in orphan


def test_an_unknown_id_is_the_unreadable_page_at_503(client):
    """Current behaviour: knot's not_found surfaces as a refusal. A 404 page is a follow-up."""
    response = client(DeclaredBacklog()).get("/ticket/nope")

    assert response.status_code == 503
    assert "no ticket matching nope" in response.text


def test_an_instant_is_shown_to_the_minute_and_nothing_as_a_dash():
    assert _humanise("2026-09-13T21:45:04.037646Z") == "2026-09-13 21:45"
    assert _humanise(None) == "—"
```

`tests/panel/test_unreadable.py`:
```python
"""The page that admits the backlog could not be read."""

from tests.panel.declared import RefusingBacklog


def test_a_backlog_that_cannot_be_read_renders_the_refusal_and_its_advice_at_503(client):
    response = client(RefusingBacklog()).get("/")

    assert response.status_code == 503
    assert "no knot project here" in response.text
    assert "run knot init, or point elsewhere" in response.text
```

- [ ] **Step 6: Live**

`tests/panel/test_live.py`:
```python
"""The one-way stream that says when the backlog changed."""

from tests.panel.declared import DeclaredBacklog


def test_the_digest_is_served_as_text(client):
    response = client(DeclaredBacklog(digests=["d1"])).get("/digest")

    assert (response.status_code, response.text) == (200, "d1")


def test_the_stream_says_changed_waits_says_changed_again_and_ends_when_the_backlog_goes(client):
    """Digests A, A, B, then nothing: a changed event, a keepalive comment, a second changed
    event, an unreadable event, and the generator ends itself. The list() returning is the
    assertion that it ended."""
    backlog = DeclaredBacklog(digests=["A", "A", "B"])
    with client(backlog, heartbeat=0).stream("GET", "/live") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        lines = [line for line in response.iter_lines() if line]

    assert lines == [
        "event: changed", "data: A",
        ": waiting",
        "event: changed", "data: B",
        "event: unreadable", "data: the tickets directory went away",
    ]
    assert backlog.digest_calls == 4
```
With the Task 6 `digest` (pop, then raise on empty), the third call returns B and the fourth raises.

- [ ] **Step 7: Run**

Run: `devenv shell -- pytest tests/panel -q --no-cov`
Expected: all pass; the stream test finishes in well under a second.

- [ ] **Step 8: Commit**

`git add tests && git commit -m "test(panel): every page asserted over a declared backlog"`

---

### Task 9: The real knot, for fidelity

**Files:**
- Create: `tests/reading/test_real_knot.py`

- [ ] **Step 1: Test**

```python
"""The real knot against the recorded envelopes, so the fixtures cannot rot silently.

Fidelity only: every source line is covered by the fake. This writes ticket files directly rather
than through knot's write verbs, because this repository's ticket-discipline hook blocks bare knot
writes and the fixtures were recorded the same way.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from knotview.reading.knot_command import KnotCommand
from tests.reading.envelopes import envelope

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(shutil.which("knot") is None, reason="knot is not on PATH"),
]

TICKETS = {
    "pro-01m2aaaaaaaa--the-parent.md": """---
id: pro-01m2aaaaaaaa
title: The parent
status: open
type: epic
priority: 1
mode: hitl
created: '2026-09-01T10:00:00.000000Z'
updated: '2026-09-02T10:00:00.000000Z'
acceptance:
- title: first thing
  done: true
- title: second thing
  done: false
tags:
- p0
- auth
---
Text before any heading.

## Description
What the parent is for.

## Design
How it is built.

## Notes

**2026-09-02T10:00:00.000000Z**

A note on the parent.
""",
    "pro-01m2bbbbbbbb--the-child.md": """---
id: pro-01m2bbbbbbbb
title: The child
status: in_progress
type: task
priority: 2
mode: afk
created: '2026-09-03T10:00:00.000000Z'
updated: '2026-09-04T10:00:00.000000Z'
assignee: ''
parent: pro-01m2aaaaaaaa
deps:
- pro-01m2cccccccc
- pro-01m2zzzzzzzz
links:
- pro-01m2dddddddd
---

## Description
The child does a thing.
""",
    "pro-01m2dddddddd--the-orphan.md": """---
id: pro-01m2dddddddd
title: The orphan
status: open
type: bug
priority: 3
mode: hitl
created: '2026-09-05T10:00:00.000000Z'
updated: '2026-09-05T10:00:00.000000Z'
assignee: someone
links:
- pro-01m2bbbbbbbb
---

## Description
Filed under nothing.
""",
    "archive/pro-01m2cccccccc--the-closed-one.md": """---
id: pro-01m2cccccccc
title: The closed one
status: closed
type: chore
priority: 4
mode: hitl
created: '2026-08-01T10:00:00.000000Z'
updated: '2026-08-02T10:00:00.000000Z'
closed: '2026-08-02T10:00:00.000000Z'
parent: pro-01m2aaaaaaaa
---

## Description
Done and archived.
""",
}


@pytest.fixture(scope="module")
def probe(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("probe")
    subprocess.run(["knot", "init"], cwd=root, check=True, capture_output=True)
    (root / ".knot.edn").write_text('{:project-name "probe" :prefix "pro"}\n', encoding="utf-8")
    for name, text in TICKETS.items():
        path = root / ".tickets" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def raw(probe: Path, *verb: str) -> dict:
    answer = subprocess.run(["knot", *verb, "--json"], cwd=probe, capture_output=True, text=True)
    return json.loads(answer.stdout)


def shape(value: object) -> object:
    """Key sets and list shapes, with values dropped, so timestamps and paths do not compare."""
    if isinstance(value, dict):
        return {key: shape(held) for key, held in sorted(value.items())}
    if isinstance(value, list):
        return [shape(held) for held in value]
    return type(value).__name__


@pytest.mark.parametrize(
    ("name", "verb"),
    [
        ("info", ("info",)),
        ("list", ("list",)),
        ("closed", ("closed",)),
        ("ready", ("ready",)),
        ("blocked", ("blocked",)),
        ("show-parent", ("show", "pro-01m2aaaaaaaa")),
        ("show-child", ("show", "pro-01m2bbbbbbbb")),
        ("check-issues", ("check",)),
        ("not-found", ("show", "nope")),
    ],
)
def test_the_binary_still_emits_the_recorded_shape(probe: Path, name: str, verb: tuple[str, ...]):
    assert shape(raw(probe, *verb)) == shape(envelope(name))


def test_the_reader_over_the_binary_agrees_with_the_reader_over_the_recording(probe: Path):
    command = KnotCommand(repository=probe)

    assert [one.id for one in command.live()] == [row["id"] for row in envelope("list")["data"]]
    assert [one.id for one in command.ready()] == ["pro-01m2aaaaaaaa", "pro-01m2dddddddd"]
    assert [one.id for one in command.blocked()] == ["pro-01m2bbbbbbbb"]
    assert [one.id for one in command.closed()] == ["pro-01m2cccccccc"]
    child = command.ticket("pro-01m2bbbbbbbb")
    assert [b.id for b in child.blockers] == ["pro-01m2cccccccc", "pro-01m2zzzzzzzz"]
    parent = command.ticket("pro-01m2aaaaaaaa")
    assert list(parent.sections) == ["", "description", "design", "notes"]
    (line,) = command.integrity()
    assert line.startswith("pro-01m2bbbbbbbb unknown_id:")
    assert command.digest() != "absent"
```

Settled at plan review by probing knot 0.12.0: `knot init` succeeds in a bare directory, and a
`.knot.edn` written afterwards with `:prefix "pro"` is honoured by `list` and `info`.

- [ ] **Step 2: Run**

Run: `devenv shell -- pytest tests/reading/test_real_knot.py -q --no-cov`
Expected: 10 passed (the check envelope's `scanned` counts and the paths differ in value, not
shape, which `shape` ignores).

- [ ] **Step 3: Commit**

`git add tests && git commit -m "test(reading): the real knot against the recorded envelopes"`

---

### Task 10: The gate

- [ ] **Step 1: Full run**

Run: `devenv shell -- pytest`
Expected: all pass, `TOTAL ... 100%`, exit 0.

- [ ] **Step 2: Without the slow test**

Run: `devenv shell -- pytest -m "not slow"`
Expected: `TOTAL ... 100%`. If any line is uncovered here, it is covered only by the real-knot
test; add a fake-driven test for it. Do not add a pragma:
`grep -rn "pragma: no cover" src tests` must be empty.

- [ ] **Step 3: Lint what this story adds**

Run: `devenv shell -- ruff check src tests && devenv shell -- black --check src tests`
Expected: the only ruff finding is the pre-existing `C901` on `panel()` (kno-01m2ebf3w4q3). Fix
anything new under `tests/` or in the two changed source files.

- [ ] **Step 4: Commit anything the lint pass changed**

`git add -A src tests && git commit -m "test: lint pass over the new suite"` (only if there is a diff).

---

## Findings to record during execution

- `Project.is_terminal` has no caller; tested anyway (finding 5, deferred to kno-01m2ebf3w4q3).
- A missing blocker counts as open (finding 7); asserted as current behaviour.
- An unknown ticket id is a 503 (finding 8); asserted as current behaviour.
- `Tree.over` drops a live child whose parent is not live (finding 19, recorded at plan review).
