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
