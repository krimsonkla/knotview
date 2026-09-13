"""One ticket in full."""

from knotview.panel.app import _humanise
from tests.panel.declared import DeclaredBacklog


def test_the_header_carries_the_chips_the_instants_and_the_parent(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text

    assert "<h1>The child</h1>" in page
    assert 'href="/tickets?mode=afk"' in page
    assert "nobody" in page
    assert "created 2026-09-01 10:00 · updated 2026-09-04 10:00" in page
    assert '<a href="/ticket/pro-01m2aaaaaaaa">pro-01m2aaaaaaaa</a>' in page


def test_criteria_sections_tags_and_notes_are_rendered_in_the_tickets_own_order(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2aaaaaaaa").text

    assert 'acceptance <span class="num">1/2</span>' in page
    assert "✓" in page and "○" in page
    assert page.index("Text before any heading.") < page.index("What for.") < page.index("A note.")
    assert 'href="/tickets?tag=auth"' in page


def test_every_graph_direction_and_the_external_refs_are_listed(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text
    parent = client(DeclaredBacklog()).get("/ticket/pro-01m2aaaaaaaa").text

    assert "blocked by" in page and "The closed one" in page
    assert "missing" in page and "no ticket has this id" in page
    assert "linked" in page and "The orphan" in page
    assert "https://example.test/1" in page
    assert "children" in parent


def test_a_closed_ticket_shows_when_it_closed_and_an_assignee_is_a_link(client):
    closed = client(DeclaredBacklog()).get("/ticket/pro-01m2cccccccc").text
    orphan = client(DeclaredBacklog()).get("/ticket/pro-01m2dddddddd").text

    assert "closed 2026-08-02 10:00" in closed
    assert 'href="/tickets?assignee=someone"' in orphan


def test_an_unknown_id_is_a_page_that_is_not_there_at_404(client):
    """The backlog read fine; the ticket is not in it. A 404 that offers the list, not a 503."""
    response = client(DeclaredBacklog()).get("/ticket/nope")

    assert response.status_code == 404
    assert "This panel has no ticket called nope." in response.text


def test_an_instant_is_shown_to_the_minute_and_nothing_as_a_dash():
    assert _humanise("2026-09-13T21:45:04.037646Z") == "2026-09-13 21:45"
    assert _humanise(None) == "—"
