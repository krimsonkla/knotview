"""knot's own queues, and the page for a queue this panel does not have."""

from knotview.panel.app import _waves
from tests.panel.declared import DeclaredBacklog, ticket


def test_ready_and_blocked_list_their_tickets(client):
    ready = client(DeclaredBacklog()).get("/queue/ready").text
    blocked = client(DeclaredBacklog()).get("/queue/blocked").text

    assert "Every blocker closed" in ready and "The parent" in ready and "The child" not in ready
    assert (
        "Ordered by how many tickets closing each one frees" in ready
        and "rounds of closing" in blocked
    )
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

    assert page.index("ready once today") < page.index("Soon")
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


def test_the_ready_queue_leads_with_what_frees_most_then_priority_then_id(client):
    few = ticket("pro-01m2ffffffff", title="Frees few", leverage=1, priority=0)
    urgent = ticket("pro-01m2uuuuuuuu", title="Frees most urgent", leverage=5, priority=0)
    later = ticket("pro-01m2llllllll", title="Frees most later", leverage=5, priority=3)
    tied = ticket("pro-01m2kkkkkkkk", title="Frees most tied", leverage=5, priority=3)
    leaf = ticket("pro-01m2aaaaaaaa", title="Frees nothing", leverage=0, priority=0)
    backlog = DeclaredBacklog(ready_value=(leaf, few, later, tied, urgent))

    page = client(backlog).get("/queue/ready").text
    order = ["Frees most urgent", "Frees most tied", "Frees most later", "Frees few"]

    assert [page.index(title) for title in order] == sorted(page.index(t) for t in order)
    assert page.index("Frees few") < page.index("Frees nothing")


def test_each_ready_row_says_how_much_it_frees_and_a_leaf_says_nothing(client):
    one = ticket("pro-01m2oooooooo", title="Frees one", leverage=1)
    leaf = ticket("pro-01m2aaaaaaaa", title="Frees nothing", leverage=0)

    page = client(DeclaredBacklog(ready_value=(one, leaf))).get("/queue/ready").text

    assert ">frees 1</span>" in page and "closing it frees 1 ticket waiting on it" in page
    assert page.count(">frees 1<") == 1 and "frees 0" not in page


def test_the_blocked_queue_keeps_its_rows_free_of_what_they_would_free(client):
    waiting = ticket("pro-01m2wwwwwwww", title="Waiting", leverage=4, level=1)

    page = client(DeclaredBacklog(blocked_value=(waiting,))).get("/queue/blocked").text

    assert "Waiting" in page and "frees" not in page
