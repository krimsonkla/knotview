"""The one-way stream that says when the backlog changed."""

from itertools import islice

from tests.panel.declared import DeclaredBacklog


def test_the_digest_is_served_as_text(client):
    response = client(DeclaredBacklog(digests=["d1"])).get("/digest")

    assert (response.status_code, response.text) == (200, "d1")


def test_the_stream_says_changed_waits_says_changed_again_and_ends_when_the_backlog_goes(client):
    """Digests A, A, B, then nothing: a changed event, a keepalive comment, a second changed
    event, an unreadable event, and the generator ends itself. The read is capped at eight
    lines, so a regression that keeps the stream open fails on the sequence rather than hanging."""
    backlog = DeclaredBacklog(digests=["A", "A", "B"])
    with client(backlog, heartbeat=0).stream("GET", "/live") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        lines = list(islice((line for line in response.iter_lines() if line), 8))

    assert lines == [
        "event: changed",
        "data: A",
        ": waiting",
        "event: changed",
        "data: B",
        "event: unreadable",
        "data: the tickets directory went away",
    ]
    assert backlog.digest_calls == 4
