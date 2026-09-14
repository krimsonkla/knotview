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
from knotview.values.unreadable_backlog import UnreadableBacklog
from tests.reading.envelopes import RECORDINGS, envelope

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


def raw(probe: Path, command: str, arguments: tuple[str, ...]) -> dict:
    """One envelope straight from the binary, spoken as the reader speaks it."""
    spoken = [*command.split(), "--json", *(["--", *arguments] if arguments else [])]
    answer = subprocess.run(
        ["knot", *spoken], cwd=probe, capture_output=True, text=True, check=False
    )
    return json.loads(answer.stdout)


def shape(value: object) -> object:
    """Key sets and list shapes, with values dropped, so timestamps and paths do not compare."""
    if isinstance(value, dict):
        return {key: shape(held) for key, held in sorted(value.items())}
    if isinstance(value, list):
        return [shape(held) for held in value]
    return type(value).__name__


def agrees(recorded: object, actual: object) -> list[str]:
    """Where the binary's shape departs from the recording, as paths; empty when it agrees.

    Additive: knot documents that new keys arrive without a version bump, so a key the binary
    adds is not a departure, while a recorded key that is missing or changed type is. A value the
    recording holds as a string may come back null, since the probe's git identity is the
    recorder's and a runner has none.
    """
    return list(_departures(recorded, actual, ""))


def _departures(recorded: object, actual: object, at: str):
    if isinstance(recorded, dict):
        yield from _mapping_departures(recorded, actual, at)
    elif isinstance(recorded, list):
        yield from _list_departures(recorded, actual, at)
    elif recorded != actual and not (recorded == "str" and actual == "NoneType"):
        yield f"{at}: {actual} where {recorded} was recorded"


def _mapping_departures(recorded: dict, actual: object, at: str):
    if not isinstance(actual, dict):
        yield f"{at}: {type(actual).__name__} where a mapping was recorded"
        return
    for key, held in recorded.items():
        if key not in actual:
            yield f"{at}.{key}: missing"
        else:
            yield from _departures(held, actual[key], f"{at}.{key}")


def _list_departures(recorded: list, actual: object, at: str):
    if not isinstance(actual, list):
        yield f"{at}: {type(actual).__name__} where a list was recorded"
        return
    for index, held in enumerate(recorded[: len(actual)]):
        yield from _departures(held, actual[index], f"{at}[{index}]")
    if len(actual) != len(recorded):
        yield f"{at}: {len(actual)} entries where {len(recorded)} were recorded"


@pytest.mark.parametrize(("name", "command", "arguments"), RECORDINGS)
def test_the_binary_still_emits_the_recorded_shape(
    probe: Path, name: str, command: str, arguments: tuple[str, ...]
):
    assert not agrees(shape(envelope(name)), shape(raw(probe, command, arguments)))


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
    with pytest.raises(UnreadableBacklog, match="no ticket matching -x"):
        command.ticket("-x")
    assert command.digest() != "absent"
