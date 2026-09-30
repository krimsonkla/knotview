"""The refusal raised when knot has no document for an identifier."""

from knotview.values.unreadable_backlog import UnreadableBacklog


class MissingDocument(UnreadableBacklog):
    """knot read the backlog fine and found no document by that identifier.

    A kind of the general refusal, as a missing ticket is, and its own class because its page is
    different: a 404 offering the ticket list, since the likeliest cause is a link to a document
    since deleted, rather than a 503 about a backlog that cannot be read.
    """

    def __init__(self, identifier: str, *, message: str) -> None:
        super().__init__(
            message,
            advice="open the ticket that owned it and check its documents; knot also resolves the "
            "start of a document id",
            code="doc_not_found",
        )
        self.identifier = identifier
