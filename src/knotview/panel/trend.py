"""The backlog over the last few weeks, worked out from the instants each ticket already carries.

knotview keeps no history: it reads, and a history would have to be written somewhere. What each
ticket does record is when it was created and, once terminal, when it closed. Those two instants
are enough to say how many tickets were open at the end of any past week, how many were opened
and closed in it, and how long closed work took. They are not enough for anything that changed in
between: a ticket's past status, priority or type is not recorded, so time in progress and past
blocking cannot be told from these files, and nothing here pretends to.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from statistics import median

from knotview.values.ticket import Ticket

# Twelve weeks is a quarter: long enough to show a trend, short enough that each week keeps a
# readable column on a chart a quarter of the page wide.
WEEKS = 12


@dataclass(frozen=True, kw_only=True)
class Week:
    """One week, Monday to Sunday in UTC: what was opened and closed in it, and what stayed open.

    `open` is counted at the week's end, or at the moment of reading for the week still running,
    so the last column always equals the live count a reader sees in the headline.
    """

    start: date
    opened: int
    closed: int
    open: int


@dataclass(frozen=True, kw_only=True)
class Lead:
    """How long tickets of one kind took from created to closed, as a median.

    A median rather than a mean, because one ticket left open for a season would otherwise move
    the figure for every quick fix closed beside it.
    """

    label: str
    seconds: float
    count: int

    @property
    def spoken(self) -> str:
        """The median in the unit a reader would say it in.

        Work an agent opens and closes in one sitting takes minutes, and "0.0 days" would hide
        that, so the unit follows the size: minutes within the hour, hours within the day, then
        days to one decimal.
        """
        minutes = self.seconds / 60
        if minutes < 60:
            return f"{max(1, round(minutes))} min"
        if minutes < 60 * 24:
            return f"{round(minutes / 60)} h"
        return f"{minutes / (60 * 24):.1f} days"


@dataclass(frozen=True, kw_only=True)
class Trend:
    """The last weeks of the backlog, and the lead time of what closed in them.

    Counted from the same live and closed tickets the overview holds, so it narrows with the
    reader's tags and costs no further knot read. A ticket without a readable `created` instant
    is left out of every count rather than placed in a week it may not belong to.
    """

    weeks: tuple[Week, ...]
    lead: Lead | None
    lead_by_type: tuple[Lead, ...]

    @classmethod
    def over(
        cls,
        live: tuple[Ticket, ...],
        closed: tuple[Ticket, ...],
        types: tuple[str, ...],
        *,
        now: datetime,
        weeks: int = WEEKS,
    ) -> "Trend":
        """The trend of these tickets over at most that many weeks, ending with this one."""
        spans = [
            (made, _instant(one.closed), one.type)
            for one in live + closed
            if (made := _instant(one.created)) is not None
        ]
        starts = _starts(spans, now, weeks)
        first = datetime.combine(starts[0], datetime.min.time(), UTC)
        done = [(made, ended, kind) for made, ended, kind in spans if ended and ended >= first]
        return cls(
            weeks=tuple(_week(start, spans, now) for start in starts),
            lead=_lead("all", [ended - made for made, ended, _ in done]),
            lead_by_type=tuple(
                lead
                for kind in types
                if (lead := _lead(kind, [e - m for m, e, k in done if k == kind])) is not None
            ),
        )

    @property
    def shown(self) -> bool:
        """Whether there is anything to draw: a week with work opened, closed or still open."""
        return any(week.opened or week.closed or week.open for week in self.weeks)

    @property
    def most_open(self) -> int:
        """The tallest open column, so every column is drawn against the same height."""
        return max((week.open for week in self.weeks), default=0) or 1

    @property
    def most_moved(self) -> int:
        """The tallest opened or closed column, for the same reason."""
        return max((max(week.opened, week.closed) for week in self.weeks), default=0) or 1

    @property
    def longest(self) -> float:
        """The slowest kind's median, so the lead time bars share one scale."""
        return max((lead.seconds for lead in self.lead_by_type), default=0.0) or 1.0


def _starts(spans: list, now: datetime, weeks: int) -> list[date]:
    """The Mondays of the weeks to draw, oldest first, ending with the week still running.

    A backlog younger than the window starts at its first ticket's week, since the weeks before
    it would only be empty columns that read as a quiet quarter.
    """
    monday = (now - timedelta(days=now.weekday())).date()
    earliest = min((made for made, _, _ in spans), default=now)
    first_monday = (earliest - timedelta(days=earliest.weekday())).date()
    reach = max(1, min(weeks, (monday - first_monday).days // 7 + 1))
    return [monday - timedelta(weeks=back) for back in range(reach - 1, -1, -1)]


def _week(start: date, spans: list, now: datetime) -> Week:
    """One week counted from every ticket's created and closed instants."""
    begin = datetime.combine(start, datetime.min.time(), UTC)
    end = min(begin + timedelta(weeks=1), now)
    return Week(
        start=start,
        opened=sum(1 for made, _, _ in spans if begin <= made < end),
        closed=sum(1 for _, ended, _ in spans if ended and begin <= ended < end),
        open=sum(1 for made, ended, _ in spans if made < end and (ended is None or ended >= end)),
    )


def _lead(label: str, took: list[timedelta]) -> Lead | None:
    """The median of those durations, or nothing when nothing closed."""
    if not took:
        return None
    return Lead(label=label, seconds=median(one.total_seconds() for one in took), count=len(took))


def _instant(stamped: str | None) -> datetime | None:
    """An instant knot wrote, or nothing when it is missing or cannot be read as one."""
    if not stamped:
        return None
    try:
        held = datetime.fromisoformat(stamped.replace("Z", "+00:00"))
    except ValueError:
        return None
    return held if held.tzinfo else held.replace(tzinfo=UTC)
