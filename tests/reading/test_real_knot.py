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
- {title: first thing, done: true}
- {title: second thing, done: false}
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


@pytest.fixture(name="probe", scope="module")
def probe_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A knot project holding the same tickets the fixtures were recorded from."""
    root = tmp_path_factory.mktemp("probe")
    subprocess.run(["knot", "init"], cwd=root, check=True, capture_output=True)
    # Only the prefix, so the ids match; the name stays null as it was when recorded.
    (root / ".knot.edn").write_text('{:prefix "pro"}\n', encoding="utf-8")
    for name, text in TICKETS.items():
        path = root / ".tickets" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def raw(probe: Path, *verb: str) -> dict:
    """One envelope straight from the binary."""
    answer = subprocess.run(
        ["knot", *verb, "--json"], cwd=probe, capture_output=True, text=True, check=False
    )
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
