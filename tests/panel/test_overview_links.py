"""Every count on the overview equals the list its link opens, whatever the overview's URL holds.

The overview counts the backlog through the reader's tags and nothing else, so its links carry
nothing else: a filter left in the overview's own URL once rode into every card's link while the
counts ignored it, and a card could say "chore 0" and open a list of one closed chore.
"""

import html
import re
from dataclasses import replace
from urllib.parse import urlsplit

import pytest

from knotview.values.document import Document
from tests.panel.declared import PROJECT, DeclaredBacklog, ticket

# A live chore, a closed chore, a ticket owning an other document and an unassigned one, so every
# card has a row above zero; built here rather than by editing the shared declared backlog.
LIVE_CHORE = ticket("pro-01m2l1111111", type="chore", assignee="someone")
OWNER = ticket(
    "pro-01m2l2222222",
    doc_types=("other",),
    assignee="someone",
    documents=(
        Document(id="pro-01m2l2222222-d1x", ticket="pro-01m2l2222222", title="Note", type="other"),
    ),
)
UNASSIGNED = ticket("pro-01m2l3333333", type="bug", status="in_progress")
CLOSED_CHORE = ticket("pro-01m2l4444444", type="chore", status="closed")
BACKLOG = {
    "project_value": replace(PROJECT, doc_types=("spec", "plan", "other"), doc_count=1),
    "live_value": (LIVE_CHORE, OWNER, UNASSIGNED),
    "closed_value": (CLOSED_CHORE,),
    "ready_value": (LIVE_CHORE, OWNER),
    "blocked_value": (UNASSIGNED,),
    "documents_value": {},
}
FILTERED = "/?closed=1&type=bug&doc=spec&assignee=someone&q=z&lacking=1"


def rows(page: str) -> list[tuple[str, str, int]]:
    """Each card row on the overview as (card, href, count), read from the rendered tallies."""
    found = []
    for card in re.finditer(
        r"<h2>([^<]+)</h2>\s*(?:<p[^>]*>[^<]*</p>\s*)?<ul class=\"tally\">(.*?)</ul>", page, re.S
    ):
        for href, count in re.findall(
            r'<a href="([^"]+)"\s*>[^<]+</a\s*>\s*<span class="num">(\d+)</span>', card.group(2)
        ):
            found.append((card.group(1), html.unescape(href), int(count)))
    return found


def listed(page: str) -> int:
    """How many tickets a list or queue page draws."""
    return page.count("<tr data-updated")


@pytest.fixture(name="browser")
def overview_browser(client):
    """A client over the backlog every card has a non-zero row in."""
    return client(DeclaredBacklog(**BACKLOG))


def test_every_card_has_a_row_to_follow(browser):
    cards = {card for card, _, count in rows(browser.get("/").text) if count}

    assert {"by type", "by status", "by priority", "by document", "queues"} <= cards


@pytest.mark.parametrize("start", ["/", FILTERED])
def test_every_count_equals_the_list_its_link_opens(browser, start):
    """Followed as a reader would: each row's link is opened and its tickets counted."""
    followed = rows(browser.get(start).text)

    assert followed
    for card, href, count in followed:
        assert listed(browser.get(href).text) == count, f"{card}: {href}"


def test_no_filter_in_the_overviews_url_reaches_a_card_link(browser):
    """Each link holds its own row's filter and nothing more: one parameter, or a terminal
    status's two, whatever the overview's own URL was asked with."""
    for _, href, _ in rows(browser.get(FILTERED).text):
        names = sorted(name.split("=")[0] for name in urlsplit(href).query.split("&") if name)
        assert len(names) <= 1 or names == ["closed", "status"], href


def test_a_filter_in_the_overviews_url_changes_nothing(browser):
    """Apart from the tag bar's way back, which returns the reader to the URL they were on."""
    back = re.compile(r'name="back" value="[^"]*"')

    assert back.sub("", browser.get(FILTERED).text) == back.sub("", browser.get("/").text)


def test_each_card_link_carries_exactly_its_rows_own_filter(browser):
    hrefs = {href for _, href, _ in rows(browser.get(FILTERED).text)}

    assert {
        "/tickets?type=chore",
        "/tickets?status=open",
        "/tickets?status=closed&closed=1",
        "/tickets?priority=2",
        "/tickets?doc=other",
        "/queue/ready",
        "/tickets?assignee=nobody",
    } <= hrefs
