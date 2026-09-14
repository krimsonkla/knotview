"""The tags a reader has chosen to see the whole backlog through."""

from dataclasses import dataclass

from knotview.values.ticket import Ticket

# The cookie the chosen tags travel in. A cookie because the choice is the reader's, not the
# backlog's: it lives in their browser, follows them from page to page, and is never written
# anywhere the panel reads tickets from. The panel stays read-only over the backlog.
COOKIE = "knotview_tags"

# Tags are joined with a character knot does not allow in a tag, so the cookie splits cleanly.
_SEPARATOR = ","


@dataclass(frozen=True, kw_only=True)
class Tags:
    """The tags every view is narrowed to, in the order they were chosen.

    A ticket matches when it carries all of them, which is what narrowing means: choosing a second
    tag makes the view smaller, never larger. Nothing chosen means nothing narrowed.
    """

    chosen: tuple[str, ...] = ()

    @classmethod
    def from_cookie(cls, held: str | None) -> "Tags":
        """The tags a cookie carries, ignoring blanks and repeats however the cookie was edited."""
        seen: list[str] = []
        for tag in (held or "").split(_SEPARATOR):
            clean = tag.strip()
            if clean and clean not in seen:
                seen.append(clean)
        return cls(chosen=tuple(seen))

    def cookie(self) -> str:
        """This choice as the cookie carries it."""
        return _SEPARATOR.join(self.chosen)

    def adding(self, tag: str) -> "Tags":
        """This choice with that tag, once, or unchanged for a blank."""
        clean = tag.strip().replace(_SEPARATOR, "")
        if not clean or clean in self.chosen:
            return self
        return Tags(chosen=(*self.chosen, clean))

    def dropping(self, tag: str) -> "Tags":
        """This choice without that tag."""
        return Tags(chosen=tuple(one for one in self.chosen if one != tag.strip()))

    def matches(self, ticket: Ticket) -> bool:
        """Whether that ticket carries every chosen tag."""
        return all(tag in ticket.tags for tag in self.chosen)

    def narrow(self, tickets: tuple[Ticket, ...]) -> tuple[Ticket, ...]:
        """Those tickets that carry every chosen tag, in the order given."""
        if not self.chosen:
            return tickets
        return tuple(one for one in tickets if self.matches(one))
