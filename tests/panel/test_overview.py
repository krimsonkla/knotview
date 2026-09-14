"""The first page: the backlog counted the ways a reader asks about it."""

import re

from knotview.reading.knot_command import _described
from knotview.values.attention import Attention
from tests.panel.declared import CHILD, DeclaredBacklog, ticket
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
