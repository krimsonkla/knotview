"""knot's own queues, and the page for a queue this panel does not have."""

from tests.panel.declared import DeclaredBacklog


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
