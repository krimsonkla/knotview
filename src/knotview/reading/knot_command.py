"""The backlog, read by running knot in the project it belongs to."""

import hashlib
import json
import subprocess
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from knotview.reading.knot_envelope import (
    answered,
    attention_from,
    dependency_from,
    document_from,
    documents_from,
    project_from,
    ticket_from,
    tickets_from,
    verdict,
)
from knotview.values.project import Project
from knotview.values.attention import Attention
from knotview.values.dependency import Dependency
from knotview.values.document import Document
from knotview.values.issue import Issue
from knotview.values.missing_document import MissingDocument
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
# "dep tree" is two words on purpose: knot's dep verb writes, its tree subcommand reads, and only
# the read is spoken here.
READS = (
    "info",
    "list",
    "closed",
    "ready",
    "blocked",
    "show",
    "check",
    "prime",
    "dep tree",
    "document list",
    "document show",
)


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
        self._where: Where | None = None
        self._locating = threading.Lock()

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

    def attention(self) -> Attention:
        """What knot's primer says to look at first: ready to close, and stale."""
        return attention_from(self._read("prime"))

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

    def documents(self, ticket_id: str) -> tuple[Document, ...]:
        """The documents one ticket owns, with when each was created and last updated.

        An unknown ticket is a missing ticket, as it is for a read of the ticket itself.
        """
        try:
            stated = self._read("document list", ticket_id)
        except UnreadableBacklog as refusal:
            if refusal.code == "not_found":
                raise MissingTicket(ticket_id, message=refusal.message) from refusal
            raise
        return documents_from(stated, attempting=f"listing the documents of {ticket_id}")

    def document(self, document_id: str) -> Document:
        """One document in full, body included, by the id or the partial id knot resolves.

        knot names an unknown document with its own code, so it is its own refusal and its own
        page; anything else knot refuses is a backlog that could not be read. knot resolves the
        start of an id, so the document returned may carry a longer id than the one asked for, and
        a start that several ids share names no one document, which is the same refusal.
        """
        try:
            stated = self._read("document show", document_id)
        except UnreadableBacklog as refusal:
            if refusal.code in ("doc_not_found", "ambiguous_doc"):
                raise MissingDocument(document_id, message=refusal.message) from refusal
            raise
        return document_from(stated)

    def dependencies(self, identifier: str) -> Dependency:
        """The tree of what one ticket waits on, as knot draws it, with a missing root as such."""
        return dependency_from(self._read("dep tree", identifier))

    def integrity(self) -> tuple[Issue, ...]:
        """What the project's own check reports, as issues, empty when it is clean.

        Shown rather than enforced. This panel is a reader: a backlog with a dangling reference is
        something its author wants to know about, and refusing to render until it is fixed would
        hide the very thing the reader came to see.
        """
        stated = self._read("check", verdict_read=True)
        issues = stated.get("issues") if isinstance(stated, dict) else None
        if not isinstance(issues, list):
            return ()
        root = self._located().root
        return tuple(_issue(issue, root) for issue in issues)

    def digest(self) -> str:
        """A value over the ticket files' names and modification times, so a change moves it.

        Over the files rather than over the rendered pages, because it has to be cheap enough to
        compute on a timer: this is what every open page polls, and a digest that cost a full
        read would make following the backlog more expensive than reading it. For the same reason
        the tickets directory is asked of knot once and remembered: it is a fact about the project
        that does not move while the panel runs, and asking every second would start a process per
        tick per open page.

        Modification times rather than contents, for the same reason. A write that leaves a file
        byte-identical changes nothing a reader would see. A file that vanishes between being listed
        and being stamped, which an agent closing a ticket does, is simply left out of that digest.
        """
        where = self._located()
        if not where.tickets.is_dir():
            return "absent"
        trees = [("", where.tickets)]
        # Documents live inside the tickets directory unless `.knot.edn` moves them; only then is
        # there a second tree, and walking the default one twice would double every tick's cost.
        if where.docs.is_dir() and not where.docs.is_relative_to(where.tickets):
            trees.append(("docs:", where.docs))
        stamped = sorted(
            f"{mark}{stamp}"
            for mark, tree in trees
            for stamp in (_stamped(tree, path) for path in tree.rglob("*.md"))
            if stamp
        )
        return hashlib.sha256("\n".join(stamped).encode("utf-8")).hexdigest()[:16]

    def _located(self) -> "Where":
        """Where the tickets, the documents and the project are, asked of knot once and kept.

        Pages read the backlog from several threads at once, so the first asking is locked: the
        tabs that open together with the panel then start one `knot info` between them, not one
        each.
        """
        with self._locating:
            if self._where is None:
                self._where = Where.of(self.project())
            return self._where

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
            return [self._knot, *command.split(), "--json"]
        return [self._knot, *command.split(), "--json", "--", *arguments]


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


@dataclass(frozen=True, kw_only=True)
class Where:
    """The three places a project's files are, as knot stated them when first asked."""

    tickets: Path
    docs: Path
    root: Path

    @classmethod
    def of(cls, project: Project) -> "Where":
        """The places knot's info names, with knot's own defaults for any it leaves out.

        A knot that states no docs path keeps documents in the tickets directory, and one that
        states no root is rooted where the tickets directory sits; defaulting to an empty path
        instead would make the working directory a tree the digest walks.
        """
        tickets = Path(project.tickets_path)
        return cls(
            tickets=tickets,
            docs=Path(project.docs_path) if project.docs_path else tickets / "docs",
            root=Path(project.project_root) if project.project_root else tickets.parent,
        )


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
    where = " ".join(_named(issue.get("ids")))
    code = issue.get("code")
    message = issue.get("message")
    if not (where or code or message):
        return json.dumps(issue)
    head = " ".join(part for part in (where, str(code) if code else "") if part)
    return f"{head}: {message}" if head and message else (head or str(message))


# What an issue's ids mean, surveyed from knot 0.15.0's check.clj rather than read off the codes'
# names: its `:ids` names the records an issue is about, while the offending value rides in
# `:field` and `:value`. Re-survey these when knot is upgraded.
#
# Codes whose ids are documents `document show` serves. legacy_documents_section names a ticket,
# and duplicate_doc_id an id knot refuses as ambiguous, so neither is here.
LINKED = frozenset(
    {"doc_unknown_ticket", "invalid_doc_type", "doc_directory_mismatch", "doc_id_owner_mismatch"}
)
# Codes whose ids are tickets. unknown_id names its holder; the missing target is only in the
# message, and linking it would open a page for the one id known to resolve to nothing. dep_cycle
# names every ticket on the cycle with the first repeated to close it, and its message spells the
# path, so linking each once loses nothing. missing_required_field is emitted by the ticket tier
# ([id], or [] with no id) and the document tier (always []): it is safe only while the document
# tier stays empty, so it is the first to re-check on an upgrade. Codes whose ids are always empty
# (unreachable_documents, invalid_active_status, skill_stale, frontmatter_parse_error) are in
# neither set, so that a knot which starts filling them cannot make the panel link wrongly.
TICKET_CODES = frozenset(
    {
        "invalid_status",
        "invalid_type",
        "invalid_mode",
        "invalid_priority",
        "terminal_outside_archive",
        "unknown_id",
        "acceptance_invalid",
        "legacy_acceptance_section",
        "reserved_section",
        "duplicate_section",
        "legacy_documents_section",
        "missing_required_field",
        "dep_cycle",
    }
)


def _named(ids: object) -> tuple[str, ...]:
    """An issue's ids that name something: strings, not empty, each once, in knot's order.

    knot's contract says an id is never null, but it emits `ids: [null]` for invalid_priority and
    terminal_outside_archive on a ticket with no id; such an id is neither linked nor written.
    """
    if not isinstance(ids, list):
        return ()
    return tuple(dict.fromkeys(one for one in ids if isinstance(one, str) and one))


def _issue(issue: object, root: Path) -> Issue:
    """One check entry as an issue: its line, its path from the project, and what it links."""
    if not isinstance(issue, dict):
        return Issue(text=_described(issue))
    code = issue.get("code")
    named = _named(issue.get("ids"))
    documents = named if code in LINKED else ()
    tickets = named if code in TICKET_CODES else ()
    path = issue.get("path")
    # A linked issue's ids are drawn as its links, so its line leaves them out rather than
    # naming each record twice.
    text = _described(
        {key: value for key, value in issue.items() if key != "ids"}
        if documents or tickets
        else issue
    )
    return Issue.found(
        text, path if isinstance(path, str) else "", root, documents, ticket_ids=tickets
    )
