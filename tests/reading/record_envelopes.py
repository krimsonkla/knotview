"""Re-record the envelopes under tests/reading/envelopes from the knot on PATH.

    uv run python -m tests.reading.record_envelopes

Builds the probe project the fidelity test uses and runs every command in RECORDINGS, in four
stages: record every answer into memory, normalize the fields known to carry machine values,
guard the whole set, and write only if the guard passes. So a recording carries no home
directory, no scratch path and no user name, and a refused run leaves the fixtures untouched.
Run it after upgrading knot, then run the suite: the reader tests say whether the shapes still
read, and the fidelity test says whether the recordings match. CI never runs it; CI only checks
the recordings against the tagged knot.
"""

import json
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

from tests.reading.envelopes import HERE, RECORDINGS
from tests.reading.probe import DOCUMENTS, TICKETS, write_probe

SCRUBBED_ROOT = "/probe"

# The clean probe: the parent and its archived child, named exactly. The live child names a
# dependency that does not exist, and the orphan links to the live child, so either would make
# the check report. write_probe drops the documents whose owner is left out, so none is orphaned.
CLEAN_TICKETS = (
    "pro-01m2aaaaaaaa--the-parent.md",
    "archive/pro-01m2cccccccc--the-closed-one.md",
)
SCRUBBED_ASSIGNEE = "someone"


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
    # Four spaces, as .editorconfig asks of JSON, so a re-recording diffs only where knot changed.
    return json.dumps(held, indent=4) + "\n"


def leaks(recordings: dict[str, str], forbidden: Iterable[str | None]) -> list[tuple[str, str]]:
    """Each recording that still holds a forbidden string, with the string it holds.

    An empty or missing value is not searched for: an unset git name would otherwise match every
    recording and refuse every run.
    """
    needles = sorted({needle for needle in forbidden if needle})
    return [
        (name, needle)
        for name in sorted(recordings)
        for needle in needles
        if needle in recordings[name]
    ]


def vetted(recordings: dict[str, str], forbidden: Iterable[str | None]) -> list[str]:
    """Every reason not to write this set: a leak, or a clean check that reports issues."""
    problems = [f"{name} contains {needle}" for name, needle in leaks(recordings, forbidden)]
    if "check-clean" in recordings:
        issues = json.loads(recordings["check-clean"])["data"]["issues"]
        if issues:
            problems.append(f"check-clean reports {len(issues)} issue" + "s" * (len(issues) > 1))
    return problems


def finish(
    recordings: dict[str, str], forbidden: Iterable[str | None], write: Callable[[str], None]
) -> int:
    """Write every recording, or none: refuse the whole set when anything is wrong with it."""
    problems = vetted(recordings, forbidden)
    for problem in problems:
        print(f"refused: {problem}", file=sys.stderr)
    if problems:
        return 1
    for name in sorted(recordings):
        write(name)
    return 0


def forbidden_strings(scratch: str) -> set[str]:
    """What no recording may contain: the scratch directory in both its spellings, the home
    directory, and the name git would sign with.

    Only `info`'s paths and assignee are normalized. knot also writes absolute paths into the
    `path` and `message` of a `check` issue, so a recording that captures a document issue would
    be refused here; normalize those fields before recording one.
    """
    return {scratch, str(Path(scratch).resolve()), str(Path.home()), git_user_name()}


def git_user_name() -> str:
    """The name git would sign with here, or nothing when it has none."""
    try:
        answered = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True, check=False
        )
    except OSError:
        return ""
    return answered.stdout.strip()


def main() -> int:
    """Record every envelope, then write them all or none, printing each file written."""
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch, "probe")
        root.mkdir()
        write_probe(root, TICKETS, DOCUMENTS)
        clean = Path(scratch, "clean")
        clean.mkdir()
        write_probe(clean, {name: TICKETS[name] for name in CLEAN_TICKETS}, DOCUMENTS)
        recordings = {
            name: scrubbed(name, answer(root, command, arguments), root)
            for name, command, arguments in RECORDINGS
        }
        recordings["check-clean"] = scrubbed("check-clean", answer(clean, "check", ()), clean)
        forbidden = forbidden_strings(scratch)

        def write(name: str) -> None:
            (HERE / f"{name}.json").write_text(recordings[name], encoding="utf-8")
            print(f"recorded {name}.json")

        return finish(recordings, forbidden, write)


if __name__ == "__main__":
    sys.exit(main())
