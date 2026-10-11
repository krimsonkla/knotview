"""The tickets page's filters: canonical URLs, chips for every filter, and counts per option."""

import re

import pytest

from knotview.panel.selection import Selection
from tests.panel.declared import DeclaredBacklog, ticket

BUGS = tuple(ticket(f"kno-b{n}", type="bug", status="open", tags=("teams",)) for n in range(3))
TASKS = tuple(ticket(f"kno-t{n}", type="task", status="open") for n in range(2))
SHUT = ticket("kno-c1", type="task", status="closed")


def _chip(page: str, label: str) -> bool:
    """Whether the page shows a removable chip with that label, whatever its markup."""
    return re.search(rf">\s*{re.escape(label)}\s*<a", page) is not None


def _client(client):
    return client(DeclaredBacklog(live_value=BUGS + TASKS, closed_value=(SHUT,)))


def test_a_non_canonical_query_redirects_to_the_canonical_one(client):
    answer = _client(client).get("/tickets?type=any&status=open&q=", follow_redirects=False)

    assert answer.status_code == 303
    assert answer.headers["location"] == "/tickets?status=open"


def test_an_empty_canonical_query_redirects_to_the_bare_path(client):
    answer = _client(client).get("/tickets?type=any", follow_redirects=False)

    assert answer.status_code == 303 and answer.headers["location"] == "/tickets"


@pytest.mark.parametrize(
    "state",
    [
        {"status": "open"},
        {"docs": ("spec", "plan")},
        {"deep": True},
        {"tag": "no-such-tag"},
        {"order": "leverage"},
        {"closed": True, "status": "closed"},
        {"query": "a b+c/é&x", "deep": True},
        {"assignee": "nobody"},
        {},
    ],
)
def test_the_canonical_url_is_a_fixed_point(client, state):
    canonical = Selection(**state).query_string()

    answer = _client(client).get(
        f"/tickets?{canonical}" if canonical else "/tickets", follow_redirects=False
    )

    assert answer.status_code == 200, canonical


@pytest.mark.parametrize(
    "path", ["/?type=any", "/tree?x=1", "/queue/ready?type=any", "/digest?a=b"]
)
def test_no_other_route_redirects_on_its_query(client, path):
    assert _client(client).get(path, follow_redirects=False).status_code in (200, 503)


def test_pill_options_count_under_the_other_filters(client):
    page = _client(client).get("/tickets?status=open").text

    assert 'value="bug">bug (3)</option>' in page
    assert 'value="task">task (2)</option>' in page


def test_an_applied_terminal_status_stays_selected_without_include_closed(client):
    page = _client(client).get("/tickets?status=closed").text

    assert '<option value="closed" selected>closed' in page
    assert ">status closed<" in page.replace("\n", "")


def test_closed_and_in_text_have_chips_and_dropping_in_text_keeps_the_query(client):
    page = _client(client).get("/tickets?q=bug&deep=1&closed=1").text

    assert _chip(page, "include closed") and _chip(page, "in text")
    assert 'href="/tickets?q=bug&amp;closed=1"' in page


def test_in_text_has_no_chip_without_a_query(client):
    page = _client(client).get("/tickets?deep=1").text

    assert not _chip(page, "in text")


def test_counts_are_taken_under_every_other_filter():
    selection = Selection(status="open", tag="teams")

    counts = selection.counted(BUGS + TASKS + (SHUT,), DeclaredBacklog().project(), "type")

    assert counts == {"bug": 3}


def test_tag_counts_count_each_tag_a_ticket_carries():
    counts = Selection().counted(BUGS + TASKS, DeclaredBacklog().project(), "tag")

    assert counts == {"teams": 3}


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("type=bug", 3),
        ("status=open", 5),
        ("priority=2", 5),
        ("mode=hitl", 0),
        ("assignee=nobody", 5),
        ("tag=teams", 3),
        ("component=1", 0),
        ("q=kno-b1", 1),
        ("q=nothing&deep=1", 0),
        ("closed=1", 6),
        ("order=title", 5),
        ("doc=spec", 0),
        ("nodocs=1", 5),
        ("type=unknown", 5),
    ],
)
def test_every_old_url_selects_what_it_did(client, query, expected):
    page = _client(client).get(f"/tickets?{query}").text

    # Counted on the attribute both the old table rows and the new rows carry, so this test
    # runs green before Task 3 changes anything: the numbers are today's behaviour.
    assert page.count("data-updated=") == expected
