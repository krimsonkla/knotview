"""A knot that answers from the recorded envelopes, so the command can be driven to every branch.

Injected through KnotCommand's own constructor rather than put on PATH: no environment leaks
between tests, and the failure modes are chosen per command by the environment the fixture sets.
"""

import stat
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from knotview.reading.knot_command import KnotCommand
from tests.reading.envelopes import HERE as ENVELOPES

SCRIPT = f"""#!{sys.executable}
import json, os, sys, time
from pathlib import Path

ENVELOPES = Path({str(ENVELOPES)!r})
verb = sys.argv[1] if len(sys.argv) > 1 else ""
mode = os.environ.get("KNOTVIEW_FAKE_MODE", "")
if mode == "junk":
    print("not json")
    sys.exit(0)
if mode == "hang":
    time.sleep(5)
    sys.exit(0)


def say(name, code=0):
    sys.stdout.write((ENVELOPES / f"{{name}}.json").read_text(encoding="utf-8"))
    sys.exit(code)


if verb == "info":
    held = json.loads((ENVELOPES / "info.json").read_text(encoding="utf-8"))
    tickets = os.environ["KNOTVIEW_FAKE_TICKETS"]
    root = str(Path(tickets).parent)
    held["data"]["paths"] = {{
        "cwd": root,
        "project_root": root,
        "config_path": root + "/.knot.edn",
        "tickets_dir": ".tickets",
        "tickets_path": tickets,
        "archive_path": tickets + "/archive",
    }}
    print(json.dumps(held))
    sys.exit(0)
if verb in ("list", "closed", "ready", "blocked"):
    say(verb)
if verb == "check":
    which = os.environ.get("KNOTVIEW_FAKE_CHECK", "clean")
    if which == "issues":
        say("check-issues")
    if which == "empty":
        print(json.dumps({{"schema_version": 1, "ok": False, "data": {{"issues": []}}}}))
        sys.exit(1)
    if which == "error":
        say("not-found", 1)
    if which == "bare":
        print(json.dumps({{"schema_version": 1, "ok": True, "data": {{}}}}))
        sys.exit(0)
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
sys.stderr.write(f"fake knot: unknown verb {{verb}}\\n")
sys.exit(2)
"""


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
