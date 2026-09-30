"""How an open page learns the backlog changed: it asks for a digest, and holds no stream."""

import inspect

from fastapi.routing import APIRoute

from knotview.panel.app import HERE, panel
from knotview.values.missing_document import MissingDocument
from knotview.values.missing_ticket import MissingTicket
from knotview.values.unreadable_backlog import UnreadableBacklog
from tests.panel.declared import DeclaredBacklog

FOLLOW = (HERE / "static" / "follow.js").read_text(encoding="utf-8")


def test_the_digest_is_served_as_text(client):
    response = client(DeclaredBacklog(digests=["d1"])).get("/digest")

    assert (response.status_code, response.text) == (200, "d1")


def test_a_backlog_that_cannot_be_read_answers_the_digest_with_a_refusal(client):
    response = client(DeclaredBacklog(digests=[])).get("/digest")

    assert response.status_code == 503


def test_the_page_asks_for_the_digest_and_holds_no_stream_open():
    """A stream per tab used up the six connections a browser allows one host, and the next
    page waited behind them; short requests leave the connections free."""
    assert 'fetch("/digest", { cache: "no-store" })' in FOLLOW
    assert "EventSource" not in FOLLOW
    assert "document.hidden" in FOLLOW and "visibilitychange" in FOLLOW


def test_no_route_or_refusal_page_is_a_coroutine_so_knot_reads_run_off_the_event_loop():
    """A coroutine that starts knot holds the event loop: every tab's poll and every other page
    waited behind one mistyped ticket id for as long as knot took to answer."""
    app = panel(DeclaredBacklog())
    routes = [route for route in app.routes if isinstance(route, APIRoute)]

    assert not [route.path for route in routes if inspect.iscoroutinefunction(route.endpoint)]
    ours = [
        app.exception_handlers[kind] for kind in (UnreadableBacklog, MissingTicket, MissingDocument)
    ]
    assert not [handler for handler in ours if inspect.iscoroutinefunction(handler)]


def test_a_hidden_tab_still_learns_what_it_was_rendered_from():
    assert "(document.hidden && known !== null) || asking" in FOLLOW


def test_a_panel_that_stops_answering_is_asked_less_often():
    assert "wait = Math.min(wait * 2, LONGEST)" in FOLLOW and "setTimeout(ask, wait)" in FOLLOW
