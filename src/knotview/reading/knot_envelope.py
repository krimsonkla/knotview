"""Reading knot's own answer shape, and turning it into this panel's values."""

from typing import Any

from knotview.values.criterion import Criterion
from knotview.values.project import Project
from knotview.values.reference import Reference
from knotview.values.ticket import Ticket
from knotview.values.unreadable_backlog import UnreadableBacklog

# The envelope version this panel was written against. knot wraps every answer in
# {schema_version, ok, data} and says so in its own documentation, so a version that moves is a
# signal rather than a surprise: the shape below may have changed, and guessing would be worse than
# saying so.
SCHEMA = 1


def answered(payload: dict[str, Any], *, attempting: str) -> Any:
    """The data out of one knot envelope, refusing an envelope that says it failed.

    The refusal carries knot's own message where it gave one, because knot already says the useful
    thing: which id was not found, which project is missing, which value was not allowed.
    """
    _versioned(payload, attempting=attempting)
    if not payload.get("ok"):
        raise _refused(payload, attempting=attempting)
    return payload.get("data")


def verdict(payload: dict[str, Any], *, attempting: str) -> Any:
    """The data out of knot's check, whose ok is a health verdict rather than a success flag.

    knot documents one carve-out from the envelope rule: check emits ok:false together with data
    whenever the project has issues, because ok answers "is the project healthy" there. So a
    not-ok check that carries a non-empty issues list is an answer, and the issues are what the
    reader came for. A not-ok check with no issues is a scan that failed, and stays a refusal:
    reading it as a clean project would hide exactly the failure the check exists to report.
    """
    _versioned(payload, attempting=attempting)
    if payload.get("ok"):
        return payload.get("data")
    stated = payload.get("data")
    if isinstance(stated, dict) and isinstance(stated.get("issues"), list) and stated["issues"]:
        return stated
    raise _refused(payload, attempting=attempting)


def _versioned(payload: Any, *, attempting: str) -> None:
    """Refuse anything that is not an envelope of the version this panel was written against."""
    if not isinstance(payload, dict):
        raise UnreadableBacklog(
            f"{attempting} answered with {type(payload).__name__} rather than an envelope",
            advice="check the knot version against the one this panel was written for",
        )
    if payload.get("schema_version") != SCHEMA:
        raise UnreadableBacklog(
            f"{attempting} answered with envelope version {payload.get('schema_version')!r} "
            f"rather than {SCHEMA}",
            advice="check whether knot's answer shape moved, and update this panel deliberately",
        )


def _refused(payload: dict[str, Any], *, attempting: str) -> UnreadableBacklog:
    """The refusal for a not-ok envelope, carrying knot's message where it gave one."""
    stated = payload.get("error") or {}
    said = stated.get("message") if isinstance(stated, dict) else None
    return UnreadableBacklog(
        f"{attempting} was refused: {said or 'knot gave no reason'}",
        advice="run the same knot command in that directory to see it in full",
    )


def project_from(stated: Any) -> Project:
    """The project's own configuration, which is what every page's navigation is built from."""
    if not isinstance(stated, dict):
        raise UnreadableBacklog(
            "the project reported no configuration",
            advice="check that the directory holds a knot project, with knot info",
        )
    described = _mapping(stated, "project")
    allowed = _mapping(stated, "allowed_values")
    paths = _mapping(stated, "paths")
    counts = _mapping(stated, "counts")
    span = _mapping(allowed, "priority_range")
    return Project(
        name=str(described.get("name") or "unnamed"),
        prefix=str(described.get("prefix") or ""),
        knot_version=str(described.get("knot_version") or "unknown"),
        types=_words(allowed, "types"),
        statuses=_words(allowed, "statuses"),
        active_status=str(allowed.get("active_status") or ""),
        terminal_statuses=_words(allowed, "terminal_statuses"),
        modes=_words(allowed, "modes"),
        priority_range=(int(span.get("min", 0)), int(span.get("max", 0))),
        tickets_path=str(paths.get("tickets_path") or ""),
        live_count=int(counts.get("live_count") or 0),
        archive_count=int(counts.get("archive_count") or 0),
    )


def tickets_from(stated: Any, *, attempting: str) -> tuple[Ticket, ...]:
    """Every ticket in a listing, refusing an answer that is not one."""
    if not isinstance(stated, list):
        raise UnreadableBacklog(
            f"{attempting} answered with {type(stated).__name__} rather than a list of tickets",
            advice="check the knot version against the one this panel was written for",
        )
    return tuple(ticket_from(held) for held in stated if isinstance(held, dict))


def ticket_from(stated: dict[str, Any]) -> Ticket:
    """One ticket, from whichever command answered: a listing, or a full read."""
    identifier = stated.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise UnreadableBacklog(
            "a ticket was stated with no id",
            advice="run knot check in that project to find the file that cannot be read",
        )
    return Ticket(
        id=identifier,
        title=str(stated.get("title") or "(untitled)"),
        status=str(stated.get("status") or ""),
        type=str(stated.get("type") or ""),
        priority=int(stated.get("priority") or 0),
        mode=_text(stated, "mode"),
        assignee=_text(stated, "assignee"),
        parent=_text(stated, "parent"),
        created=_text(stated, "created"),
        updated=_text(stated, "updated"),
        closed=_text(stated, "closed"),
        tags=_words(stated, "tags"),
        external_refs=_words(stated, "external_refs"),
        acceptance=_criteria(stated),
        blockers=_references(stated, "blockers"),
        blocking=_references(stated, "blocking"),
        children=_references(stated, "children"),
        linked=_references(stated, "linked"),
        sections=_sections(stated),
    )


def _mapping(stated: dict[str, Any], field: str) -> dict[str, Any]:
    """One nested object, or an empty one, so a missing half does not take the page down."""
    held = stated.get(field)
    return held if isinstance(held, dict) else {}


def _words(stated: dict[str, Any], field: str) -> tuple[str, ...]:
    """A list of strings, which knot writes for types, statuses, tags and refs alike."""
    held = stated.get(field)
    if not isinstance(held, list):
        return ()
    return tuple(str(word) for word in held if isinstance(word, str | int))


def _text(stated: dict[str, Any], field: str) -> str | None:
    """One string, or nothing, with an empty string read as nothing.

    knot omits an unset assignee from both the listing and the read, and writes a blank one as an
    empty string in both, so absent and blank are the two shapes of "nobody". A panel that showed a
    blank string as a name assigned to nobody would be showing a difference that is not there.
    """
    held = stated.get(field)
    if not isinstance(held, str) or not held.strip():
        return None
    return held


def _criteria(stated: dict[str, Any]) -> tuple[Criterion, ...]:
    """The acceptance criteria, each with whether it is ticked."""
    held = stated.get("acceptance")
    if not isinstance(held, list):
        return ()
    return tuple(
        Criterion(title=str(one.get("title") or ""), done=bool(one.get("done")))
        for one in held
        if isinstance(one, dict)
    )


def _references(stated: dict[str, Any], field: str) -> tuple[Reference, ...]:
    """One direction of the graph, as the references knot states for it."""
    held = stated.get(field)
    if not isinstance(held, list):
        return ()
    return tuple(
        Reference(
            id=str(one.get("id") or ""),
            title=str(one.get("title") or ""),
            status=str(one.get("status") or ""),
        )
        for one in held
        if isinstance(one, dict) and one.get("id")
    )


def _sections(stated: dict[str, Any]) -> dict[str, str]:
    """The ticket's own headings and their text, in the order it holds them.

    Kept as the project wrote them. A ticket is a small document whose headings its author chose,
    and a panel that renamed them to fit its own layout would be editing the record while
    displaying it.
    """
    held = stated.get("sections")
    if not isinstance(held, dict):
        return {}
    return {
        str(heading): text.strip("\n")
        for heading, text in held.items()
        if isinstance(text, str) and text.strip()
    }
