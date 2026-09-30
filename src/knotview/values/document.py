"""One document a ticket carries, as this panel holds it."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Document:
    """A whole markdown file a ticket owns, such as a spec, a plan or a transcript, with a title
    and a type of its own.

    Three knot commands state a document, each saying a different amount, and the same value holds
    all three. `show` gives only the id, the title and the type of each document its ticket owns;
    `document list` adds when it was created and last updated; `document show` adds the body. So
    created, updated and body are None when knot did not state them, either because the command
    that produced this value does not report them or because the document's file lacks them, which
    knot answers with null; they are an empty string only when knot stated them as empty text. A
    page can tell "nothing to show" from "stated empty", but not which of the two reasons left it
    None.
    A type is empty when the file names none; such a document still shows, but owns no type.

    The owning ticket is always the one knot states, or the ticket that was shown, and never parsed
    out of the document's id: the id's shape is knot's to change.
    """

    id: str
    ticket: str
    title: str
    type: str
    created: str | None = None
    updated: str | None = None
    body: str | None = None
