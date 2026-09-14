"""Re-record the envelopes under tests/reading/envelopes from the knot on PATH.

    uv run python -m tests.reading.record_envelopes

Builds the probe project the fidelity test uses, runs every command in RECORDINGS, and writes the
answers with the machine-specific values scrubbed, so a recording carries no home directory, no
user name and no session identifier. Run it after upgrading knot, then run the suite: the reader
tests say whether the shapes still read, and the fidelity test says whether the recordings match.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from tests.reading.envelopes import HERE, RECORDINGS
from tests.reading.test_real_knot import TICKETS

SCRUBBED_ROOT = "/probe"
SCRUBBED_ASSIGNEE = "someone"


def probe(root: Path, tickets: dict[str, str]) -> None:
    """A knot project at that root holding those ticket files, written directly."""
    subprocess.run(["knot", "init"], cwd=root, check=True, capture_output=True)
    (root / ".knot.edn").write_text('{:prefix "pro"}\n', encoding="utf-8")
    for name, text in tickets.items():
        path = root / ".tickets" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def answer(root: Path, command: str, arguments: tuple[str, ...]) -> str:
    """knot's stdout for that command, whatever its exit status, spoken as the reader speaks it."""
    spoken = [*command.split(), "--json", *(["--", *arguments] if arguments else [])]
    return subprocess.run(
        ["knot", *spoken], cwd=root, capture_output=True, text=True, check=False
    ).stdout


def scrubbed(name: str, text: str, root: Path) -> str:
    """The recording, pretty-printed, with nothing of this machine in it.

    knot reports the project's resolved path, which on some systems is not the spelling the
    temporary directory was created under, so both spellings are scrubbed.
    """
    held = json.loads(text)
    if name == "info":
        roots = {str(root), str(root.resolve())}
        paths = held["data"]["paths"]
        for key, value in paths.items():
            for spelling in roots:
                if isinstance(value, str) and value.startswith(spelling):
                    paths[key] = SCRUBBED_ROOT + value[len(spelling) :]
        defaults = held["data"]["defaults"]
        if defaults.get("effective_create_assignee"):
            defaults["effective_create_assignee"] = SCRUBBED_ASSIGNEE
    return json.dumps(held, indent=2) + "\n"


def main() -> int:
    """Record every envelope, printing each file written."""
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch, "probe")
        root.mkdir()
        probe(root, TICKETS)
        clean = Path(scratch, "clean")
        clean.mkdir()
        # The parent and its archived child only: the live child names a dependency that does not
        # exist, and the orphan links to the live child, so either would make the check report.
        probe(
            clean,
            {name: text for name, text in TICKETS.items() if "parent" in name or "closed" in name},
        )
        for name, command, arguments in RECORDINGS:
            (HERE / f"{name}.json").write_text(
                scrubbed(name, answer(root, command, arguments), root)
            )
            print(f"recorded {name}.json")
        (HERE / "check-clean.json").write_text(
            scrubbed("check-clean", answer(clean, "check", ()), clean)
        )
        print("recorded check-clean.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
