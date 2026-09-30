"""Re-record the envelopes under tests/reading/envelopes from the knot on PATH, or check them.

    uv run python -m tests.reading.record_envelopes
    uv run python -m tests.reading.record_envelopes --check
    uv run python -m tests.reading.record_envelopes --into /some/other/directory

Builds the probe project the fidelity test uses and runs every command in RECORDINGS, in four
stages: record every answer into memory, normalize the fields known to carry machine values,
guard the whole set, and write only if the guard passes. So a recording carries no home
directory, no scratch path and no user name, and a refused run leaves the fixtures untouched.
Run it after upgrading knot, then run the suite: the reader tests say whether the shapes still
read, and the fidelity test says whether the recordings match. With `--check` it writes nothing:
it records the same way and compares each recording with its committed file, byte for byte, which
is what CI runs against the pinned knot. A shape-level fidelity test lets a hand-edited value
through; this does not.
"""

import difflib
import json
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Sequence
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

# The document-issue probe: the clean probe with three faults knot reports on documents. A
# document of a type the project does not declare (invalid_doc_type) and one naming a ticket that
# does not exist (doc_unknown_ticket), each reported with the document's id and path, and a ticket
# body with a Documents heading (legacy_documents_section), reported with the ticket's id. So the
# recording holds codes whose ids the panel links and one whose id it must not. It sits outside
# the clean-check rule in `vetted`, which holds only the recording named check-clean to no issues.
MEMO = {
    "docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d5memo--memo.md": """---
id: pro-01m2aaaaaaaa-d5memo
ticket: pro-01m2aaaaaaaa
title: Memo
type: memo
created: '2026-09-03T10:00:00.000000Z'
updated: '2026-09-03T10:00:00.000000Z'
---

A document of a type the project does not declare.
""",
}
# Written after the probe, since write_probe keeps a document only when its owner is written.
ORPHAN = {
    "docs/pro-01m2zzzzzzzz/pro-01m2zzzzzzzz-d1x--orphan.md": """---
id: pro-01m2zzzzzzzz-d1x
ticket: pro-01m2zzzzzzzz
title: Orphan
type: other
created: '2026-09-03T10:00:00.000000Z'
updated: '2026-09-03T10:00:00.000000Z'
---

A document naming a ticket that does not exist.
""",
}
PARENT = "pro-01m2aaaaaaaa--the-parent.md"


def write_faults(root: Path) -> None:
    """The clean probe at root with the three document faults: the memo, the orphan, and a
    Documents heading written by hand into the parent's body."""
    tickets = {name: TICKETS[name] for name in CLEAN_TICKETS}
    tickets[PARENT] += "\n## Documents\nWritten by hand.\n"
    write_probe(root, tickets, {**DOCUMENTS, **MEMO})
    for name, text in ORPHAN.items():
        path = root / ".tickets" / name
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding="utf-8")


RERECORD = "uv run python -m tests.reading.record_envelopes"


def answer(root: Path, command: str, arguments: tuple[str, ...]) -> str:
    """knot's stdout for that command, whatever its exit status, spoken as the reader speaks it."""
    spoken = [*command.split(), "--json", *(["--", *arguments] if arguments else [])]
    return subprocess.run(
        ["knot", *spoken], cwd=root, capture_output=True, text=True, check=False
    ).stdout


def scrubbed(name: str, text: str, spellings: Iterable[str]) -> str:
    """The recording, pretty-printed, with nothing of this machine in it.

    knot reports the project's resolved path, which on some systems is not the spelling the
    temporary directory was created under, and writes it into info's paths and into a check
    issue's path and message alike, so every spelling is replaced wherever it appears. Longest
    first: on macOS the resolved spelling holds the created one, and replacing the shorter first
    would leave /private/probe.
    """
    for spelling in sorted(set(spellings), key=len, reverse=True):
        text = text.replace(spelling, SCRUBBED_ROOT)
    held = json.loads(text)
    if name == "info":
        defaults = held["data"]["defaults"]
        if defaults.get("effective_create_assignee"):
            defaults["effective_create_assignee"] = SCRUBBED_ASSIGNEE
    # Four spaces, as .editorconfig asks of JSON, so a re-recording diffs only where knot changed.
    return json.dumps(held, indent=4) + "\n"


def compared(recordings: dict[str, str], committed: dict[str, str]) -> list[str]:
    """Every way a fresh set differs from the committed one: a file whose bytes changed, with
    its diff; a recording with no committed file; a committed file nothing records."""
    problems = []
    for name in sorted(set(recordings) | set(committed)):
        if name not in committed:
            problems.append(f"{name}.json is recorded but not committed")
        elif name not in recordings:
            problems.append(f"{name}.json is committed but nothing records it")
        elif recordings[name] != committed[name]:
            diff = difflib.unified_diff(
                committed[name].splitlines(keepends=True),
                recordings[name].splitlines(keepends=True),
                fromfile=f"committed {name}.json",
                tofile=f"recorded {name}.json",
            )
            problems.append(f"{name}.json differs:\n" + "".join(diff))
    return problems


def leaks(recordings: dict[str, str], forbidden: Iterable[str | None]) -> list[tuple[str, str]]:
    """Each recording that still holds a forbidden string, with the string it holds.

    An empty or missing value is not searched for: an unset git name would otherwise match every
    recording and refuse every run. Nor is a value the scrub itself writes: a git name of
    "probe", which CI uses, would match every /probe the scrub wrote, and a recording cannot tell
    that apart from the placeholder, so searching for it refuses every run and proves nothing.
    Only those exact values are exempt; a shorter name that merely occurs inside one, such as
    "one", is still searched for.
    """
    written = {SCRUBBED_ROOT, SCRUBBED_ROOT.strip("/"), SCRUBBED_ASSIGNEE}
    needles = sorted({needle for needle in forbidden if needle and needle not in written})
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

    The scrub now replaces the scratch directory wherever it appears, so this guard's job is
    narrower and matters more: it catches a spelling the scrub did not know, such as a symlinked
    TMPDIR or a path knot derives some other way, and it is the last thing between a machine path
    and a committed fixture.
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


def recorded(scratch: str) -> dict[str, str]:
    """Every recording, scrubbed, from the three probes built under that scratch directory."""

    def probe(name: str, tickets: dict[str, str], documents: dict[str, str]) -> Path:
        root = Path(scratch, name)
        root.mkdir()
        write_probe(root, tickets, documents)
        return root

    def faults() -> Path:
        root = Path(scratch, "faults")
        root.mkdir()
        write_faults(root)
        return root

    def spoken(name: str, root: Path, command: str, arguments: tuple[str, ...]) -> str:
        return scrubbed(name, answer(root, command, arguments), {str(root), str(root.resolve())})

    main_probe = probe("probe", TICKETS, DOCUMENTS)
    clean_tickets = {name: TICKETS[name] for name in CLEAN_TICKETS}
    clean = probe("clean", clean_tickets, DOCUMENTS)
    memo = faults()
    recordings = {
        name: spoken(name, main_probe, command, arguments)
        for name, command, arguments in RECORDINGS
    }
    recordings["check-clean"] = spoken("check-clean", clean, "check", ())
    recordings["check-documents"] = spoken("check-documents", memo, "check", ())
    return recordings


def destination(argv: Sequence[str]) -> Path:
    """Where recordings are written: the committed fixtures, or the directory after --into, so a
    fresh set can be laid beside the committed one without touching it."""
    if "--into" not in argv:
        return HERE
    if "--check" in argv:
        raise SystemExit("--check compares with the committed recordings; it takes no --into")
    at = list(argv).index("--into") + 1
    if at >= len(argv) or argv[at].startswith("-"):
        raise SystemExit("--into needs a directory")
    return Path(argv[at])


def main(argv: Sequence[str] = ()) -> int:
    """Record every envelope, then write them all or none; with --check, compare and write none."""
    checking = "--check" in argv
    into = destination(argv)
    with tempfile.TemporaryDirectory() as scratch:
        recordings = recorded(scratch)
        forbidden = forbidden_strings(scratch)

    if checking:
        # The same guard, with a writer that writes nothing, so a check cannot touch the fixtures;
        # the comparison is made here, against the committed *.json, once the guard has passed.
        refused = finish(recordings, forbidden, lambda name: None)
        if refused:
            return refused
        committed = {
            path.stem: path.read_text(encoding="utf-8") for path in sorted(HERE.glob("*.json"))
        }
        problems = compared(recordings, committed)
        for problem in problems:
            print(problem, file=sys.stderr)
        if problems:
            print(f"re-record with: {RERECORD}, then review and commit", file=sys.stderr)
            return 1
        print(f"all {len(recordings)} recordings match")
        return 0

    def write(name: str) -> None:
        into.mkdir(parents=True, exist_ok=True)
        (into / f"{name}.json").write_text(recordings[name], encoding="utf-8")
        print(f"recorded {into / name}.json")

    return finish(recordings, forbidden, write)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
