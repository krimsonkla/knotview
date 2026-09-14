"""knot's own queues, and the page for a queue this panel does not have."""

from knotview.panel.app import _waves
from tests.panel.declared import DeclaredBacklog, ticket


def test_ready_and_blocked_list_their_tickets(client):
    ready = client(DeclaredBacklog()).get("/queue/ready").text
    blocked = client(DeclaredBacklog()).get("/queue/blocked").text

    assert "Every blocker closed" in ready and "The parent" in ready and "The child" not in ready
    assert "highest leverage" in ready and "rounds of closing" in blocked
    assert "At least one blocker still open" in blocked and "The child" in blocked


def test_an_unknown_queue_is_a_page_that_says_so_at_200(client):
    response = client(DeclaredBacklog()).get("/queue/soon")

    assert response.status_code == 200
    assert "This panel has no queue called soon." in response.text


def test_the_blocked_queue_is_grouped_by_level_with_cycles_last(client):
    soon = ticket("pro-01m2ssssssss", title="Soon", level=1)
    later = ticket("pro-01m2llllllll", title="Later", level=3)
    looped = ticket("pro-01m2oooooooo", title="Looped")
    page = client(DeclaredBacklog(blocked_value=(later, looped, soon))).get("/queue/blocked").text

    assert page.index("next: ready once") < page.index("Soon")
    assert page.index("Soon") < page.index("3 rounds away") < page.index("Later")
    assert page.index("Later") < page.index("on a cycle") < page.index("Looped")


def test_waves_as_a_value_and_an_empty_queue_has_none():
    a, b, c = ticket("a", level=2), ticket("b", level=1), ticket("c")

    assert [(level, [t.id for t in ts]) for level, ts in _waves((a, b, c))] == [
        (1, ["b"]),
        (2, ["a"]),
        (None, ["c"]),
    ]
    assert not _waves(())


def test_the_ready_queue_is_not_grouped(client):
    page = client(DeclaredBacklog()).get("/queue/ready").text

    assert "rounds away" not in page and "on a cycle" not in page
