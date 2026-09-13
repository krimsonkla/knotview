"""One ticket pointing at another: a blocker, a child, a link."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Reference:
    """Another ticket, as the one referring to it sees it.

    Three fields because that is all knot gives on a reference, and all a reader needs to decide
    whether to follow it: what it is, what it is called, and whether it is still open. The status is
    the one that earns its place, since a blocker that is closed is not blocking anything.
    """

    id: str
    title: str
    status: str
