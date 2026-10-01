"""An epic's children by status, with the closed ones hidden when the reader asks."""

import re

from knotview.values.reference import Reference
from tests.panel.declared import PROJECT, DeclaredBacklog, ticket


def child(name: str, status: str, *, missing: bool = False) -> Reference:
    """One child reference, named for what it is."""
    return Reference(id=f"pro-01m2c{name}", title=f"Child {name}", status=status, missing=missing)


# Knot's order, deliberately unsorted: three live, four closed, one undeclared, one missing.
CHILDREN = (
    child("closed1", "closed"),
    child("open1", "open"),
    child("closed2", "closed"),
    child("weird", "parked"),
    child("prog1", "in_progress"),
    child("closed3", "closed"),
    child("gone", "", missing=True),
    child("open2", "open"),
    child("closed4", "closed"),
)
EPIC = ticket("pro-01m2epic0000", type="epic", title="The epic", children=CHILDREN)


def page(client, query: str = "", epic=EPIC) -> str:
    """The epic's page, with the given query."""
    return client(DeclaredBacklog(live_value=(epic,))).get(f"/ticket/{epic.id}{query}").text


def card(text: str) -> str:
    """The children card alone, whitespace folded."""
    graph = text[text.index('<section class="graph">') :]
    at = graph.index(">children<") if ">children<" in graph else graph.index("children")
    start = graph.rindex('<div class="card">', 0, at)
    return re.sub(r"\s+", " ", graph[start : graph.index("</div>", at)])


def order(text: str) -> list[str]:
    """The children's ids in the order the card lists them."""
    return re.findall(r'<span class="id">(pro-01m2c\w+)</span>', card(text))


def heading(text: str) -> str:
    """What the card's heading says, tags dropped."""
    h2 = card(text)
    h2 = h2[h2.index("<h2") : h2.index("</h2>")]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h2)).strip()


def test_children_list_in_declared_status_order_with_knots_order_kept_within_each(client):
    assert order(page(client)) == [
        "pro-01m2copen1",
        "pro-01m2copen2",
        "pro-01m2cprog1",
        "pro-01m2cclosed1",
        "pro-01m2cclosed2",
        "pro-01m2cclosed3",
        "pro-01m2cclosed4",
        "pro-01m2cweird",
        "pro-01m2cgone",
    ]


def test_shown_the_heading_counts_them_all_and_offers_to_hide_the_closed(client):
    text = page(client)

    assert heading(text) == "children 9 hide closed (4)"
    assert f'href="/ticket/{EPIC.id}?children=live"' in card(text)


def test_hidden_the_closed_children_go_and_the_heading_says_how_many_of_how_many(client):
    text = page(client, "?children=live")

    assert "pro-01m2cclosed1" not in order(text) and len(order(text)) == 5
    assert heading(text) == "children 5 of 9 show closed"
    assert f'href="/ticket/{EPIC.id}"' in card(text)


def test_the_toggle_goes_there_and_back(client):
    browser = client(DeclaredBacklog(live_value=(EPIC,)))
    shown = browser.get(f"/ticket/{EPIC.id}").text
    hide = re.search(r'href="([^"]*children=live)"', card(shown)).group(1)
    hidden = browser.get(hide).text
    show = re.search(r'href="(/ticket/[^"?]+)"[^>]*>\s*show closed', card(hidden)).group(1)

    assert heading(shown) == "children 9 hide closed (4)"
    assert heading(hidden) == "children 5 of 9 show closed"
    assert heading(browser.get(show).text) == "children 9 hide closed (4)"


def test_an_all_closed_epic_keeps_its_card_and_its_way_back(client):
    shut = ticket("pro-01m2epic0000", type="epic", children=CHILDREN[0:1] + CHILDREN[2:3])

    text = page(client, "?children=live", epic=shut)

    assert heading(text) == "children 0 of 2 show closed" and not order(text)


def test_an_unknown_value_shows_every_child(client):
    assert len(order(page(client, "?children=bogus"))) == 9


def test_no_closed_child_means_no_toggle(client):
    young = ticket("pro-01m2epic0000", type="epic", children=CHILDREN[1:2] + CHILDREN[4:5])

    assert heading(page(client, epic=young)) == "children 2"


def test_no_link_but_the_toggle_carries_the_choice(client):
    """The tag bar's way back holds this page's own URL, as on every page, and is not a link."""

    def links(text: str) -> list[str]:
        return [href for href in re.findall(r'href="([^"]*)"', text) if "children=" in href]

    assert not links(page(client, "?children=live"))
    assert links(page(client)) == [f"/ticket/{EPIC.id}?children=live"]


def test_siblings_list_by_status_and_count_what_they_draw(client):
    epic = ticket("pro-01m2epic0000", type="epic", children=CHILDREN[:6])
    me = ticket("pro-01m2cprog1", status="in_progress", parent=epic.id)
    browser = client(DeclaredBacklog(live_value=(epic, me), project_value=PROJECT))

    text = browser.get(f"/ticket/{me.id}").text
    siblings = text[text.index("also under") : text.index("</section>", text.index("also under"))]

    ids = re.findall(r'<span class="id">(pro-01m2c\w+)</span>', siblings)
    assert ids == [
        "pro-01m2copen1",
        "pro-01m2cclosed1",
        "pro-01m2cclosed2",
        "pro-01m2cclosed3",
        "pro-01m2cweird",
    ]
    assert f'<span class="num">{len(ids)}</span>' in siblings
