"""Envelopes recorded from knot 0.12.0 on a probe project, one file per command shape.

Recorded rather than written, so the tests assert the shape knot actually emits. The probe held
a parent with two children (one archived), an orphan, a blank assignee and an absent one, a
blocker that is closed and one that is missing, a symmetric link, and one dangling dependency so
the check reports an issue. test_real_knot.py re-derives the same shapes from the binary.

To re-record them against a newer knot, with knot on PATH:

    uv run python -m tests.reading.record_envelopes

The recorder builds the same probe project in a temporary directory, runs each command in
RECORDINGS, and writes the answers here with the machine-specific values scrubbed: every path
under info's `paths` is rewritten under /probe and the effective assignee becomes "someone", so a
recording never carries the recorder's home directory or name.
"""

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

# Which command each recording is the answer to. The clean check comes from a second probe that
# holds no dangling dependency, since the first exists to make the check report one.
RECORDINGS = (
    ("info", ("info",)),
    ("list", ("list",)),
    ("closed", ("closed",)),
    ("ready", ("ready",)),
    ("blocked", ("blocked",)),
    ("show-parent", ("show", "pro-01m2aaaaaaaa")),
    ("show-child", ("show", "pro-01m2bbbbbbbb")),
    ("check-issues", ("check",)),
    ("not-found", ("show", "nope")),
)


def envelope(name: str) -> dict[str, Any]:
    """One recorded envelope, by the file's stem."""
    return json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
