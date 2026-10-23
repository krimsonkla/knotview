"""The overview's progress by tag: each tag's closed tickets out of all that carry it."""

import html
import re

from knotview.panel.overview import Overview, TagProgress
from knotview.reading.snapshot import Snapshot
from tests.panel.declared import DeclaredBacklog, ticket

LIVE = (
    ticket("pro-01m2t1111111", tags=("ui", "api")),
    ticket("pro-01m2t2222222", tags=("api",)),
    ticket("pro-01m2t3333333", tags=("api",)),
)
CLOSED = (
    ticket("pro-01m2t4444444", status="closed", tags=("ui",)),
    ticket("pro-01m2t5555555", status="closed", tags=("ui", "docs")),
)


def card(page: str) -> str:
    """The by-tag card alone, so a count elsewhere on the page cannot satisfy an assertion."""
    start = page.index('data-chart="by tag"')
    return page[start : page.index("</section>", start)]


def tag_rows(page: str) -> list[tuple[str, str, str, str]]:
    """Each row of the card as (href, tag, done, total), as a reader sees them."""
    return [
        (html.unescape(href), html.unescape(tag), done, total)
        for href, tag, done, total in re.findall(
            r'<a class="kv-bar" href="([^"]+)" data-card="by tag"[^>]*><span>([^<]*)</span>'
            r'.*?<span class="kv-muted">(\d+) of</span><span class="kv-num">(\d+)</span>',
            card(page),
            re.S,
        )
    ]


def test_each_tag_counts_its_closed_tickets_out_of_all_that_carry_it(client):
    page = client(DeclaredBacklog(live_value=LIVE, closed_value=CLOSED)).get("/").text

    assert tag_rows(page) == [
        ("/tickets?tag=api&closed=1", "api", "0", "3"),
        ("/tickets?tag=ui&closed=1", "ui", "2", "3"),
        ("/tickets?tag=docs&closed=1", "docs", "1", "1"),
    ]


def test_the_bar_fills_with_the_share_closed(client):
    page = client(DeclaredBacklog(live_value=LIVE, closed_value=CLOSED)).get("/").text

    assert '<span class="kv-fill done" style="width: 67%">' in card(page)
    assert '<span class="kv-fill done" style="width: 100%">' in card(page)


def test_each_tags_count_equals_the_list_its_row_opens(client):
    browser = client(DeclaredBacklog(live_value=LIVE, closed_value=CLOSED))

    for href, tag, _, total in tag_rows(browser.get("/").text):
        assert browser.get(href).text.count('class="kv-row" data-updated') == int(total), tag


def test_the_tag_card_waits_behind_the_charts_menu(client):
    page = client(DeclaredBacklog(live_value=LIVE, closed_value=CLOSED)).get("/").text

    assert '<section class="kv-card" data-chart="by tag" hidden>' in page
    assert 'data-chart-toggle="by tag" />' in page


def test_no_tag_card_or_choice_when_no_ticket_carries_a_tag(client):
    plain = (ticket("pro-01m2t6666666"),)
    page = client(DeclaredBacklog(live_value=plain, closed_value=())).get("/").text

    assert 'data-chart="by tag"' not in page and 'data-chart-toggle="by tag"' not in page


def test_a_pinned_tag_is_left_out_and_the_rest_narrow_with_it(client):
    browser = client(DeclaredBacklog(live_value=LIVE, closed_value=CLOSED))
    browser.get("/tags?add=ui&back=/")

    assert tag_rows(browser.get("/").text) == [
        ("/tickets?tag=api&closed=1", "api", "0", "1"),
        ("/tickets?tag=docs&closed=1", "docs", "1", "1"),
    ]


def test_a_pinned_tags_rows_still_equal_their_lists(client):
    browser = client(DeclaredBacklog(live_value=LIVE, closed_value=CLOSED))
    browser.get("/tags?add=ui&back=/")

    for href, tag, _, total in tag_rows(browser.get("/").text):
        assert browser.get(href).text.count('class="kv-row" data-updated') == int(total), tag


def test_no_tag_card_when_every_tag_is_pinned(client):
    only = (ticket("pro-01m2t7777777", tags=("ui",)),)
    browser = client(DeclaredBacklog(live_value=only, closed_value=()))
    browser.get("/tags?add=ui&back=/")

    assert 'data-chart-toggle="by tag"' not in browser.get("/").text


def test_tags_past_the_eighth_fold_under_a_count_of_the_rest(client):
    many = tuple(
        ticket(f"pro-01m2m{i:07d}", tags=tuple(f"tag{n:02d}" for n in range(i + 1)))
        for i in range(10)
    )
    page = client(DeclaredBacklog(live_value=many, closed_value=())).get("/").text
    shown = card(page)
    folded = shown[shown.index("<details") :]

    assert len(tag_rows(page)) == 10
    assert "<summary>2 more tags</summary>" in folded
    assert 'data-fold="overview-tags"' in folded
    assert "tag=tag08&" in folded and "tag=tag09&" in folded and "tag=tag07&" not in folded


def test_eight_tags_draw_no_fold(client):
    eight = (ticket("pro-01m2m8888888", tags=tuple(f"tag{n}" for n in range(8))),)
    page = client(DeclaredBacklog(live_value=eight, closed_value=())).get("/").text

    assert "<details" not in card(page)


def test_ties_order_by_size_then_name():
    snapshot = Snapshot.read(
        DeclaredBacklog(
            live_value=(ticket("pro-01m2o1111111", tags=("b", "a")),),
            closed_value=(ticket("pro-01m2o2222222", status="closed", tags=("c",)),),
        )
    )

    assert Overview.over(snapshot).by_tag == (
        TagProgress(tag="a", done=0, total=1),
        TagProgress(tag="b", done=0, total=1),
        TagProgress(tag="c", done=1, total=1),
    )


def test_a_tag_is_escaped_in_its_label_and_encoded_in_its_link(client):
    odd = (ticket("pro-01m2x1111111", tags=('a&b <"x">',)),)
    browser = client(DeclaredBacklog(live_value=odd, closed_value=()))
    page = browser.get("/").text

    assert "<span>a&amp;b &lt;&#34;x&#34;&gt;</span>" in card(page)
    assert 'href="/tickets?tag=a%26b%20%3C%22x%22%3E&amp;closed=1"' in card(page)
    assert browser.get(tag_rows(page)[0][0]).text.count('class="kv-row" data-updated') == 1
