"""What knot's primer says wants a person's attention first."""

from dataclasses import dataclass

from knotview.values.ticket import Ticket


@dataclass(frozen=True, kw_only=True)
class Attention:
    """The two things knot's primer reports that nothing else does.

    A ticket is ready to close when it is in the active status and every acceptance criterion is
    ticked: the closing is the only work left, and knot's own advice is to close these before
    picking up new work. A ticket is stale when it has been in progress for two weeks without a
    change, which is knot's sign that somebody started it and stopped. Both come from knot rather
    than being recomputed here, so the panel agrees with what the CLI tells an agent.
    """

    in_progress: tuple[Ticket, ...]
    ready_to_close: tuple[Ticket, ...]
    stale: tuple[Ticket, ...]
