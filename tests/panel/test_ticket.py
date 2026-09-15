"""One ticket in full."""

from knotview.panel.app import _humanise, _is_instant
from tests.panel.declared import DeclaredBacklog, ticket


def test_the_header_carries_the_chips_the_instants_and_the_parent(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text

    assert "<h1>The child</h1>" in page
    assert 'href="/tickets?mode=afk"' in page
    assert "nobody" in page
    assert (
        '<span class="when">created <time class="stamp" datetime="2026-09-01T10:00:00.000000Z" '
        'title="2026-09-01T10:00:00.000000Z">2026-09-01 10:00 UTC</time></span>' in page
    )
    assert (
        '<span class="when">updated <time class="stamp" datetime="2026-09-04T10:00:00.000000Z" '
        'title="2026-09-04T10:00:00.000000Z">2026-09-04 10:00 UTC</time></span>' in page
    )
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

    assert (
        '<span class="when">closed <time class="stamp" datetime="2026-08-02T10:00:00.000000Z" '
        'title="2026-08-02T10:00:00.000000Z">2026-08-02 10:00 UTC</time></span>' in closed
    )
    assert 'href="/tickets?assignee=someone"' in orphan


def test_an_absent_instant_leaves_its_clause_out_and_emits_no_time_element(client):
    bare = ticket("pro-01m2eeeeeeee", created=None, updated=None)
    later = ticket("pro-01m2gggggggg", created=None)
    page = client(DeclaredBacklog(live_value=(bare,))).get("/ticket/pro-01m2eeeeeeee").text
    mixed = client(DeclaredBacklog(live_value=(later,))).get("/ticket/pro-01m2gggggggg").text

    header = page.split("<h1>")[1].split("</header>")[0]
    assert "created" not in header and "<time" not in page
    heading = mixed.split("<h1>")[1].split("</header>")[0]
    assert '<span class="when">updated <time' in heading and "·" not in heading


def test_a_dated_note_heading_is_a_stamp_and_an_undated_one_is_not(client):
    noted = ticket(
        "pro-01m2ffffffff",
        sections={"notes": "Written by hand.\n\n**2026-09-12T06:44:01.672814Z**\n\nSaid later."},
    )
    page = client(DeclaredBacklog(live_value=(noted,))).get("/ticket/pro-01m2ffffffff").text

    assert (
        '<time class="stamp" datetime="2026-09-12T06:44:01.672814Z" '
        'title="2026-09-12T06:44:01.672814Z">2026-09-12 06:44 UTC</time>' in page
    )
    assert "undated" in page and page.count("<time") == 3


def test_an_unknown_id_is_a_page_that_is_not_there_at_404(client):
    """The backlog read fine; the ticket is not in it. A 404 that offers the list, not a 503."""
    response = client(DeclaredBacklog()).get("/ticket/nope")

    assert response.status_code == 404
    assert "This panel has no ticket called nope." in response.text


def test_only_a_full_utc_instant_counts_as_one():
    assert _is_instant("2026-09-13T21:45:04.037646Z") and _is_instant("2026-09-13T21:45:04Z")
    assert not _is_instant(None) and not _is_instant("")
    assert not _is_instant("2026-09-12") and not _is_instant("wontfix")
    assert not _is_instant("2026-09-14T14:30:12+02:00") and not _is_instant("2026-09-14T14:30:12")
    assert not _is_instant("2026-99-99T99:99:99Z")


def test_a_note_heading_that_is_not_an_instant_is_shown_as_written(client):
    held = ticket(
        "pro-01m2hhhhhhhh",
        sections={"notes": "**wontfix**\n\nNot doing it.\n\n**2026-09-12**\n\nA bare date."},
    )
    page = client(DeclaredBacklog(live_value=(held,))).get("/ticket/pro-01m2hhhhhhhh").text

    assert "wontfix\n" in page and "2026-09-12\n" in page
    assert "wontfix UTC" not in page and "2026-09-12 UTC" not in page
    assert page.count("<time") == 2


def test_an_instant_is_shown_to_the_minute_and_nothing_as_a_dash():
    assert _humanise("2026-09-13T21:45:04.037646Z") == "2026-09-13 21:45"
    assert _humanise(None) == "—"


def test_the_dependency_tree_is_drawn_under_the_ticket_with_a_missing_leaf(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text

    assert "depends on, all the way down" in page
    assert page.count("pro-01m2zzzzzzzz") >= 2
    assert "The closed one" in page


def test_a_ticket_with_no_dependencies_has_no_tree_section(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2dddddddd").text

    assert "depends on, all the way down" not in page


def test_notes_are_shown_as_a_timeline_newest_first(client):
    held = ticket(
        "pro-01m2nnnnnnnn",
        title="Noted",
        sections={
            "notes": "**2026-09-12T06:44:01Z**\n\nEarlier.\n\n**2026-09-13T07:42:11Z**\n\nLater."
        },
    )
    page = client(DeclaredBacklog(live_value=(held,))).get("/ticket/pro-01m2nnnnnnnn").text

    assert page.index("Later.") < page.index("Earlier.")
    assert "2026-09-13 07:42 UTC" in page and 'datetime="2026-09-13T07:42:11Z"' in page


def test_a_child_shows_its_parent_as_a_breadcrumb_and_its_siblings(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text

    assert 'under <a href="/ticket/pro-01m2aaaaaaaa">The parent</a>' in page
    assert "also under The parent" in page
    assert "The closed one" in page
    assert page.count("also under") == 1


def test_a_child_of_a_parent_that_is_not_live_says_so_without_a_link(client):
    stray = ticket("pro-01m2eeeeeeee", title="The stray", parent="pro-01m2gone")
    page = client(DeclaredBacklog(live_value=(stray,))).get("/ticket/pro-01m2eeeeeeee").text

    assert "pro-01m2gone" in page and "which is not live" in page
    assert "also under" not in page


def test_a_ticket_without_a_parent_has_no_breadcrumb(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2dddddddd").text

    assert "under <" not in page and "also under" not in page
