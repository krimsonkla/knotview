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
        "docs_path": os.environ.get("KNOTVIEW_FAKE_DOCS") or tickets + "/docs",
    }}
    print(json.dumps(held))
    sys.exit(0)
if verb in ("list", "closed", "ready", "blocked", "prime"):
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
    if which == "documents":
        # As knot 0.15 states document issues: absolute paths, one inside the project and one
        # outside it, and a warning whose id is a ticket's.
        root = str(Path(os.environ["KNOTVIEW_FAKE_TICKETS"]).parent)
        issues = [
            {{
                "severity": "error",
                "code": "invalid_doc_type",
                "ids": ["pro-01m2aaaaaaaa-d5memo"],
                "path": root + "/.tickets/docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d5memo--memo.md",
                "message": "document has type memo",
            }},
            {{
                "severity": "error",
                "code": "doc_unknown_ticket",
                "ids": ["pro-01m2zzzzzzzz-d1x"],
                "path": "/elsewhere/docs/pro-01m2zzzzzzzz/pro-01m2zzzzzzzz-d1x--orphan.md",
                "message": "names a ticket that resolves to no ticket",
            }},
            {{
                "severity": "warning",
                "code": "legacy_documents_section",
                "ids": ["pro-01m2aaaaaaaa"],
                "message": "a body carries a Documents heading",
            }},
        ]
        print(json.dumps({{"schema_version": 1, "ok": False, "data": {{"issues": issues}}}}))
        sys.exit(1)
    if which == "bare":
        print(json.dumps({{"schema_version": 1, "ok": True, "data": {{}}}}))
        sys.exit(0)
    say("check-clean")
if verb == "dep" and len(sys.argv) > 2 and sys.argv[2] == "tree":
    if sys.argv[-1] == "pro-01m2bbbbbbbb":
        say("dep-tree")
    absent = {{"id": sys.argv[-1], "missing": True}}
    print(json.dumps({{"schema_version": 1, "ok": True, "data": absent}}))
    sys.exit(0)
if verb == "document" and len(sys.argv) > 2 and sys.argv[2] == "list":
    if sys.argv[-1] == "pro-01m2aaaaaaaa":
        say("document-list")
    say("not-found", 1)
if verb == "document" and len(sys.argv) > 2 and sys.argv[2] == "show":
    if sys.argv[-1] == "pro-01m2aaaaaaaa-d7spec":
        say("document-show")
    if sys.argv[-1] == "pro-01m2aaaaaaaa-d":
        refusal = {{"code": "ambiguous_doc", "message": "more than one document starts with it"}}
        print(json.dumps({{"schema_version": 1, "ok": False, "error": refusal}}))
        sys.exit(1)
    if sys.argv[-1] == "refused":
        refusal = {{"code": "invalid_argument", "message": "a selector knot will not take"}}
        print(json.dumps({{"schema_version": 1, "ok": False, "error": refusal}}))
        sys.exit(1)
    say("document-not-found", 1)
if verb == "show":
    wanted = sys.argv[-1]
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
