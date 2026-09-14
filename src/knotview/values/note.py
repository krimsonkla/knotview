"""One note on a ticket, as knot appends them."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Note:
    """One entry of a ticket's notes: when it was written, and what it said.

    knot writes every note under the same heading, each introduced by its instant in bold on a
    line of its own. Splitting the section on those lines is what turns a wall of text into a
    history. A note with no instant, which a person wrote by hand before knot managed the section,
    keeps its place with no time.
    """

    at: str | None
    text: str
