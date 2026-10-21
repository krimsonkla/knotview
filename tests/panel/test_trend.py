"""The overview's charts over time: worked out from created and closed instants alone."""

from datetime import UTC, date, datetime

from knotview.panel.trend import Lead, Trend
from tests.panel.declared import DeclaredBacklog, ticket

# A Wednesday, so the week still running is part done.
NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)
TYPES = ("bug", "task", "chore")


def test_each_week_counts_what_opened_and_closed_in_it_and_what_stayed_open():
    live = (ticket("pro-01m2aaaaaaaa", created="2026-10-06T09:00:00Z"),)
    closed = (
        ticket(
            "pro-01m2bbbbbbbb",
            status="closed",
            created="2026-10-07T09:00:00Z",
            closed="2026-10-14T09:00:00Z",
        ),
    )

    trend = Trend.over(live, closed, TYPES, now=NOW)

    assert [week.start for week in trend.weeks] == [
        date(2026, 10, 5),
        date(2026, 10, 12),
        date(2026, 10, 19),
    ]
    assert [(week.opened, week.closed, week.open) for week in trend.weeks] == [
        (2, 0, 2),
        (0, 1, 1),
        (0, 0, 1),
    ]


def test_an_old_backlog_shows_only_the_last_twelve_weeks():
    live = (ticket("pro-01m2aaaaaaaa", created="2025-01-01T09:00:00Z"),)

    trend = Trend.over(live, (), TYPES, now=NOW)

    assert len(trend.weeks) == 12
    assert trend.weeks[-1].start == date(2026, 10, 19)
    assert all(week.open == 1 for week in trend.weeks)


def test_a_ticket_without_a_readable_created_instant_is_left_out():
    live = (
        ticket("pro-01m2aaaaaaaa", created=None),
        ticket("pro-01m2bbbbbbbb", created="yesterday"),
        ticket("pro-01m2cccccccc", created="2026-10-20T09:00:00"),
    )

    trend = Trend.over(live, (), TYPES, now=NOW)

    assert [(week.opened, week.open) for week in trend.weeks] == [(1, 1)]


def test_with_no_dated_tickets_there_is_nothing_to_draw():
    trend = Trend.over((ticket("pro-01m2aaaaaaaa", created=None),), (), TYPES, now=NOW)

    assert not trend.shown
    assert trend.lead is None and not trend.lead_by_type
    assert trend.most_open == 1 and trend.most_moved == 1 and trend.longest == 1.0


def test_lead_time_is_the_median_of_what_closed_in_the_window_by_type():
    def done(identifier, kind, created, closed):
        return ticket(identifier, type=kind, status="closed", created=created, closed=closed)

    closed = (
        done("pro-01m2aaaaaaaa", "task", "2026-10-13T09:00:00Z", "2026-10-13T09:30:00Z"),
        done("pro-01m2bbbbbbbb", "task", "2026-10-13T09:00:00Z", "2026-10-13T12:00:00Z"),
        done("pro-01m2cccccccc", "task", "2026-10-13T09:00:00Z", "2026-10-15T09:00:00Z"),
        done("pro-01m2dddddddd", "chore", "2026-10-10T09:00:00Z", "2026-10-13T09:00:00Z"),
        # Closed before the window opened, so it does not count towards lead time.
        done("pro-01m2eeeeeeee", "bug", "2025-01-01T09:00:00Z", "2025-02-01T09:00:00Z"),
    )

    trend = Trend.over((), closed, TYPES, now=NOW)

    assert trend.lead is not None and trend.lead.count == 4
    assert [(lead.label, lead.spoken, lead.count) for lead in trend.lead_by_type] == [
        ("task", "3 h", 3),
        ("chore", "3.0 days", 1),
    ]
    assert trend.longest == 3 * 86400


def test_a_lead_time_reads_in_minutes_hours_or_days():
    assert Lead(label="all", seconds=5, count=1).spoken == "1 min"
    assert Lead(label="all", seconds=19 * 60, count=1).spoken == "19 min"
    assert Lead(label="all", seconds=5 * 3600, count=1).spoken == "5 h"
    assert Lead(label="all", seconds=36 * 3600, count=1).spoken == "1.5 days"


def test_the_charts_over_time_wait_behind_the_charts_menu(client):
    lately = datetime.now(UTC).isoformat()
    closed = (ticket("pro-01m2aaaaaaaa", status="closed", created=lately, closed=lately),)
    page = client(DeclaredBacklog(closed_value=closed)).get("/").text

    for hidden in ("open over time", "opened and closed", "lead time"):
        assert f'<section class="kv-card" data-chart="{hidden}" hidden>' in page
        assert f'data-chart-toggle="{hidden}" />' in page
    assert 'title="week of ' in page
    assert "open at the end of each week" in page


def test_without_dated_tickets_no_chart_over_time_is_offered(client):
    live = (ticket("pro-01m2aaaaaaaa", created=None),)
    page = client(DeclaredBacklog(live_value=live, closed_value=())).get("/").text

    assert "open over time" not in page and "lead time" not in page


def test_with_nothing_closed_lately_the_lead_time_card_is_not_offered(client):
    live = (ticket("pro-01m2aaaaaaaa", created=datetime.now(UTC).isoformat()),)
    page = client(DeclaredBacklog(live_value=live, closed_value=())).get("/").text

    assert 'data-chart="open over time"' in page
    assert "lead time" not in page
    # One week has nothing to compare with, so no change is stated.
    assert " since the week of " not in page
