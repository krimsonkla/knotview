"""The refusal raised when knot has no ticket for an identifier."""

from knotview.values.unreadable_backlog import UnreadableBacklog


class MissingTicket(UnreadableBacklog):
    """knot read the backlog fine and found nothing by that identifier.

    A kind of the general refusal, so that whoever catches "the backlog could not be read" still
    sees it; its own class, because the page for it is different. A backlog that cannot be read is
    a 503 saying what to fix; a ticket that is not there is a 404 offering the list, since the
    likeliest cause is a stale link to something since deleted or a mistyped id.
    """

    def __init__(self, identifier: str, *, message: str) -> None:
        super().__init__(
            message,
            advice="check the id against the ticket list, since knot resolves a partial id",
            code="not_found",
        )
        self.identifier = identifier
