"""The backlog, read by running knot in the project it belongs to."""

import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from knotview.reading.knot_envelope import (
    answered,
    project_from,
    ticket_from,
    tickets_from,
    verdict,
)
from knotview.values.project import Project
from knotview.values.missing_ticket import MissingTicket
from knotview.values.ticket import Ticket
from knotview.values.unreadable_backlog import UnreadableBacklog

# The command, named rather than found, so the one place this panel reaches outside itself is one
# constant somebody can see.
KNOT = "knot"

# How long any single read may take before the panel stops waiting. A backlog read is a local
# process over a directory of small files; a read that takes longer than this is a knot that is
# wedged, and a page that waited forever would hang rather than say so.
PATIENCE = 20

# Only these are ever run. Every one is a read: knot's write verbs are create, start, status, close,
# reopen, delete, dep, undep, link, unlink, add-note, edit and update, and none of them appears here
# or anywhere else in this package. A test asserts that READS holds none of them, and that this is
# the only module in the package that can start a process.
READS = ("info", "list", "closed", "ready", "blocked", "show", "check")


class KnotCommand:
    """A backlog read by invoking knot in a directory, and nothing else.

    It reads knot's JSON rather than the ticket files, which is the decision this whole panel rests
    on. The files are markdown with frontmatter and knot owns their schema; a second parser here
    would be a second schema, and it would drift on the first release that adds a field. Asking
    knot means the panel is wrong only when knot is.

    Every command it runs is a read, and the list is declared above so a test can assert it.
    Nothing in this package holds a write verb, which is what makes read-only structural rather
    than polite.

    It caches nothing. A page is rendered per request and a request costs a few short processes over
    small files, which is cheap enough that a cache would mostly be a way for the panel to be out of
    date while looking current.
    """

    def __init__(self, *, repository: Path, knot: str = KNOT, patience: int = PATIENCE) -> None:
        self._repository = repository
        self._knot = knot
        self._patience = patience
        self._tickets_path: Path | None = None

    @property
    def repository(self) -> Path:
        """Which project this reads, which every page names so two panels cannot be confused."""
        return self._repository

    def project(self) -> Project:
        """What the project says about itself: its types, statuses, modes and counts."""
        return project_from(self._read("info"))

    def live(self) -> tuple[Ticket, ...]:
        """Every ticket that is not in a terminal status."""
        return tickets_from(self._read("list"), attempting="listing the live tickets")

    def closed(self) -> tuple[Ticket, ...]:
        """Every terminal ticket, newest closed first."""
        return tickets_from(self._read("closed"), attempting="listing the closed tickets")

    def ready(self) -> tuple[Ticket, ...]:
        """Every ticket whose blockers are all closed."""
        return tickets_from(self._read("ready"), attempting="listing the ready tickets")

    def blocked(self) -> tuple[Ticket, ...]:
        """Every ticket with at least one open blocker."""
        return tickets_from(self._read("blocked"), attempting="listing the blocked tickets")

    def ticket(self, identifier: str) -> Ticket:
        """One ticket in full, by the id or the partial id knot resolves.

        An identifier knot cannot resolve is its own refusal, so the panel can answer it as a page
        that is not there rather than as a backlog that cannot be read.
        """
        try:
            stated = self._read("show", identifier)
        except UnreadableBacklog as refusal:
            if refusal.code == "not_found":
                raise MissingTicket(identifier, message=refusal.message) from refusal
            raise
        if not isinstance(stated, dict):
            raise UnreadableBacklog(
                f"reading {identifier} answered with {type(stated).__name__} rather than a ticket",
                advice="check the id against knot list, since knot resolves a partial id",
            )
        return ticket_from(stated)

    def integrity(self) -> tuple[str, ...]:
        """What the project's own check reports, as lines, empty when it is clean.

        Shown rather than enforced. This panel is a reader: a backlog with a dangling reference is
        something its author wants to know about, and refusing to render until it is fixed would
        hide the very thing the reader came to see.
        """
        stated = self._read("check", verdict_read=True)
        issues = stated.get("issues") if isinstance(stated, dict) else None
        if not isinstance(issues, list):
            return ()
        return tuple(_described(issue) for issue in issues)

    def digest(self) -> str:
        """A value over the ticket files' names and modification times, so a change moves it.

        Over the files rather than over the rendered pages, because it has to be cheap enough to
        compute on a timer: this is what the live stream compares, and a digest that cost a full
        read would make following the backlog more expensive than reading it. For the same reason
        the tickets directory is asked of knot once and remembered: it is a fact about the project
        that does not move while the panel runs, and asking every second would start a process per
        tick per open page.

        Modification times rather than contents, for the same reason. A write that leaves a file
        byte-identical changes nothing a reader would see. A file that vanishes between being listed
        and being stamped, which an agent closing a ticket does, is simply left out of that digest.
        """
        tickets = self._tickets()
        if not tickets.is_dir():
            return "absent"
        stamped = sorted(
            stamp for stamp in (_stamped(tickets, path) for path in tickets.rglob("*.md")) if stamp
        )
        return hashlib.sha256("\n".join(stamped).encode("utf-8")).hexdigest()[:16]

    def _tickets(self) -> Path:
        """Where the ticket files are, asked of knot the first time and kept."""
        if self._tickets_path is None:
            self._tickets_path = Path(self.project().tickets_path)
        return self._tickets_path

    def _read(self, command: str, *arguments: str, verdict_read: bool = False) -> object:
        """One knot read, as data, refusing anything this panel was not written to run.

        The check is read through the verdict reader, because its ok is a health verdict rather
        than a success flag; every other read goes through the plain envelope rule.
        """
        if command not in READS:
            raise UnreadableBacklog(
                f"{command} is not one of the reads this panel runs",
                advice=f"use one of {', '.join(READS)}, since this panel only ever reads",
            )
        spoken = self._spoken(command, arguments)
        try:
            answer = subprocess.run(
                spoken,
                cwd=self._repository,
                capture_output=True,
                text=True,
                check=False,
                timeout=self._patience,
            )
        except FileNotFoundError as missing:
            raise UnreadableBacklog(
                f"{self._knot} is not on the path",
                advice="install knot (github.com/UniSoma/knot) and put it on PATH, or pass "
                "--knot with the path to it",
            ) from missing
        except subprocess.TimeoutExpired as waited:
            raise UnreadableBacklog(
                f"{self._knot} {command} did not answer within {self._patience} seconds",
                advice="run the same command in that directory to see what it is waiting for",
            ) from waited
        wrap = verdict if verdict_read else answered
        return wrap(_data_in(answer, spoken), attempting=f"{self._knot} {command}")

    def _spoken(self, command: str, arguments: Sequence[str]) -> list[str]:
        """The argument list knot is handed.

        Anything a reader typed goes after knot's own end-of-options marker, so an identifier that
        happens to start with a dash reaches knot as an identifier and never as an option. The
        JSON flag comes before the marker for the same reason: knot must read it as a flag.
        """
        if not arguments:
            return [self._knot, command, "--json"]
        return [self._knot, command, "--json", "--", *arguments]


def _data_in(answer: subprocess.CompletedProcess[str], spoken: Sequence[str]) -> dict:
    """The envelope knot printed, refusing output that is not one.

    knot prints its envelope on standard output and its diagnostics on standard error, and it
    answers with a failed envelope rather than with nothing when it refuses. So output that will
    not parse is
    a different thing from a non-zero exit: the first means the shape moved, and the second usually
    arrives with a readable envelope anyway.
    """
    try:
        return json.loads(answer.stdout)
    except json.JSONDecodeError as unreadable:
        said = (answer.stderr or answer.stdout or "").strip().splitlines()
        raise UnreadableBacklog(
            f"{' '.join(spoken)} printed nothing this panel can read"
            + (f": {said[0]}" if said else ""),
            advice="run that command in the directory the panel was pointed at",
        ) from unreadable


def _stamped(tickets: Path, path: Path) -> str | None:
    """One file's name and modification time, or nothing if it vanished since it was listed."""
    try:
        return f"{path.relative_to(tickets)}:{path.stat().st_mtime_ns}"
    except FileNotFoundError:
        return None


def _described(issue: object) -> str:
    """One integrity issue as a line, however knot chose to shape it.

    knot's check reports entries carrying ids (plural: an issue can span two tickets), a code, a
    message and sometimes a path. This states what it was given rather than insisting on that
    shape: a panel that refused to show an issue because the issue was shaped unexpectedly would
    be hiding exactly the thing worth showing.
    """
    if isinstance(issue, str):
        return issue
    if not isinstance(issue, dict):
        return str(issue)
    ids = issue.get("ids")
    where = " ".join(str(one) for one in ids) if isinstance(ids, list) else ""
    code = issue.get("code")
    message = issue.get("message")
    path = issue.get("path")
    if not (where or code or message):
        return json.dumps(issue)
    head = " ".join(part for part in (where, str(code) if code else "") if part)
    line = f"{head}: {message}" if head and message else (head or str(message))
    return f"{line} ({path})" if path else line
