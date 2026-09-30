"""Envelopes recorded from knot 0.15.0 on a probe project, one file per command shape.

Recorded rather than written, so the tests assert the shape knot actually emits. The probe, in
tests/reading/probe.py, holds a parent with two children (one archived), an orphan, a blank
assignee and an absent one, a blocker that is closed and one that is missing, a symmetric link,
and one dangling dependency so the check reports an issue. It also holds four documents: a spec
and a plan on the parent, a spec on the live child, and a note on the archived child, so every
listing carries a row that owns documents. test_real_knot.py re-derives the same shapes from the
binary.

To re-record them against a newer knot, with knot on PATH:

    uv run python -m tests.reading.record_envelopes

The recorder builds the same probe project in a temporary directory, runs each command in
RECORDINGS, normalizes the machine-specific values (every spelling of the scratch directory,
wherever it appears, becomes /probe, and the effective assignee becomes "someone"), then refuses
to write anything if a recording still holds the scratch directory, the home directory or the git
user name, or if the clean check reports an issue. Two more recordings come from their own
probes: check-clean, from one with no dangling dependency, and check-documents, from one with a
document of an undeclared type, so a check issue carrying a path is recorded. `--check` compares
instead of writing, and CI runs it against the pinned knot.
"""

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

# Which command each recording is the answer to: the recording's name, knot's command (one or two
# words), and the arguments after it. The clean check comes from a second probe that holds no
# dangling dependency, since the first exists to make the check report one.
RECORDINGS = (
    ("info", "info", ()),
    ("list", "list", ()),
    ("closed", "closed", ()),
    ("ready", "ready", ()),
    ("blocked", "blocked", ()),
    ("show-parent", "show", ("pro-01m2aaaaaaaa",)),
    ("show-child", "show", ("pro-01m2bbbbbbbb",)),
    ("check-issues", "check", ()),
    ("not-found", "show", ("nope",)),
    ("prime", "prime", ()),
    ("dep-tree", "dep tree", ("pro-01m2bbbbbbbb",)),
    ("document-list", "document list", ("pro-01m2aaaaaaaa",)),
    ("document-show", "document show", ("pro-01m2aaaaaaaa-d7spec",)),
    ("document-not-found", "document show", ("pro-01m2aaaaaaaa-dnope",)),
)


def envelope(name: str) -> dict[str, Any]:
    """One recorded envelope, by the file's stem."""
    return json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
