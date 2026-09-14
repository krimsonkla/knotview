"""The first page: the backlog counted the ways a reader asks about it."""

import re

from datetime import UTC, datetime

from knotview.panel.app import _ago
from knotview.reading.knot_command import _described
from knotview.values.criterion import Criterion
from knotview.values.attention import Attention
from tests.panel.declared import CHILD, PARENT, DeclaredBacklog, ticket
from tests.reading.envelopes import envelope


def test_every_declared_type_is_counted_even_at_zero_with_a_link_to_its_filter(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a href="/tickets?type=feature"' in page
    assert "epic" in page and "chore" in page


def test_statuses_priorities_and_queues_are_counted(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a href="/tickets?status=in_progress"' in page
    assert '<a href="/tickets?priority=3"' in page
    assert '<a href="/queue/ready">ready</a>' in page
    assert '<a href="/tickets?assignee=nobody">unassigned</a>' in page
    assert '<a href="/tickets?closed=1">1</a>' in page


def test_the_live_total_is_the_sum_over_statuses(client):
    page = client(DeclaredBacklog()).get("/").text

    assert re.search(r'<a href="/tickets">live</a\s*><span class="num">3</span>', page)


def test_parents_are_whatever_something_is_filed_under_and_closed_work_is_listed(client):
    page = client(DeclaredBacklog()).get("/").text

    assert "The parent" in page
    assert "The closed one" in page


def test_recently_closed_is_capped(client):
    many = tuple(
        ticket(f"pro-01m2{i:08d}", status="closed", title=f"Closed {i}") for i in range(10)
    )
    page = client(DeclaredBacklog(closed_value=many)).get("/").text

    assert "Closed 7" in page and "Closed 8" not in page


def test_a_clean_project_shows_no_integrity_section(client):
    assert "integrity" not in client(DeclaredBacklog()).get("/").text


def test_integrity_issues_are_listed_as_knot_reported_them_at_200(client):
    """AC 3: the line comes from the recorded check through the real formatter."""
    lines = tuple(_described(one) for one in envelope("check-issues")["data"]["issues"])

    response = client(DeclaredBacklog(integrity_value=lines)).get("/")

    assert response.status_code == 200
    assert "pro-01m2bbbbbbbb unknown_id: unknown id" in response.text


def test_ready_to_close_and_stale_are_shown_when_the_primer_reports_them(client):
    old = ticket("pro-01m2oooooooo", title="Started and stopped", status="in_progress")
    report = Attention(in_progress=(CHILD, old), ready_to_close=(CHILD,), stale=(old,))
    page = client(DeclaredBacklog(attention_value=report)).get("/").text

    assert "ready to close" in page and "close these before picking up new work" in page
    assert "stale" in page and "Started and stopped" in page


def test_neither_section_appears_when_the_primer_reports_nothing(client):
    page = client(DeclaredBacklog()).get("/").text

    assert "ready to close" not in page and "Started and stopped" not in page


def test_recently_changed_lists_live_tickets_newest_first_with_a_relative_time(client):
    page = client(DeclaredBacklog()).get("/").text

    section = page[page.index("recently changed") : page.index("recently closed")]
    assert section.index("The child") < section.index("The parent") < section.index("The orphan")
    assert 'title="2026-09-04T10:00:00.000000Z"' in section and "d ago" in section


def test_an_instant_reads_as_a_distance_from_now():
    now = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)

    assert _ago("2026-09-14T11:59:40Z", now) == "just now"
    assert _ago("2026-09-14T11:15:00Z", now) == "45 min ago"
    assert _ago("2026-09-14T03:00:00Z", now) == "9 h ago"
    assert _ago("2026-09-01T10:00:00.000000Z", now) == "13 d ago"
    assert _ago(None) == "—" and _ago("not an instant") == "not an instant"
    assert (
        _ago("2026-09-14T11:59:59Z").endswith("ago") or _ago("2026-09-14T11:59:59Z") == "just now"
    )


def test_progress_lists_parents_with_criteria_nearest_to_done_first(client):
    far = ticket(
        "pro-01m2ffffffff",
        title="Far parent",
        acceptance=tuple(Criterion(title=f"c{i}", done=False) for i in range(4)),
    )
    kid = ticket("pro-01m2kkkkkkkk", parent="pro-01m2ffffffff")
    page = client(DeclaredBacklog(live_value=(far, kid, PARENT, CHILD))).get("/").text

    section = page[page.index("<h2>progress</h2>") : page.index("<h2>parents</h2>")]
    assert section.index("The parent") < section.index("Far parent")
    assert '<progress value="1" max="2">' in section and "1/2 criteria" in section
    assert "1 live beneath" in section


def test_a_parent_without_criteria_is_not_in_progress(client):
    bare = ticket("pro-01m2pppppppp", title="Bare parent")
    kid = ticket("pro-01m2qqqqqqqq", parent="pro-01m2pppppppp")
    page = client(DeclaredBacklog(live_value=(bare, kid))).get("/").text

    assert "<h2>progress</h2>" not in page


def test_overview_cards_add_to_the_readers_current_selection(client):
    page = client(DeclaredBacklog()).get("/?type=task").text

    assert 'href="/tickets?type=task&status=in_progress"' in page
    assert 'href="/tickets?type=task&priority=3"' in page
