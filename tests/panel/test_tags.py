"""The tags a reader chooses once and sees every view through."""

from knotview.panel.tags import COOKIE, Tags
from tests.panel.declared import CHILD, ORPHAN, PARENT, DeclaredBacklog, ticket


def test_tags_round_trip_through_the_cookie_ignoring_blanks_and_repeats():
    chosen = Tags.from_cookie(" p0, auth,,p0 ")

    assert chosen.chosen == ("p0", "auth")
    assert Tags.from_cookie(chosen.cookie()) == chosen
    assert not Tags.from_cookie(None).chosen


def test_adding_and_dropping_keep_order_and_refuse_a_blank():
    chosen = Tags().adding("p0").adding(" auth ").adding("p0").adding("  ").adding("a,b")

    assert chosen.chosen == ("p0", "auth", "ab")
    assert chosen.dropping("p0").chosen == ("auth", "ab")
    assert Tags().adding("") is not None


def test_a_ticket_matches_when_it_carries_every_chosen_tag():
    both = Tags(chosen=("p0", "auth"))

    assert both.matches(PARENT) and not both.matches(CHILD)
    assert Tags(chosen=("p0",)).narrow((PARENT, CHILD, ORPHAN)) == (PARENT,)
    assert Tags().narrow((PARENT, CHILD)) == (PARENT, CHILD)


def test_adding_a_tag_sets_the_cookie_and_goes_back_to_the_page(client):
    browser = client(DeclaredBacklog())

    answer = browser.get("/tags?add=p0&back=/tree", follow_redirects=False)

    assert answer.status_code == 303 and answer.headers["location"] == "/tree"
    assert browser.cookies.get(COOKIE) == "p0"


def test_every_view_narrows_to_the_chosen_tags_until_cleared(client):
    browser = client(DeclaredBacklog())
    browser.get("/tags?add=auth&back=/")

    tickets = browser.get("/tickets").text
    overview = browser.get("/").text
    tree = browser.get("/tree").text
    ready = browser.get("/queue/ready").text

    assert "The parent" in tickets and "The child" not in tickets
    assert "1 of 1" in tickets
    assert "The parent" in overview and "The orphan" not in overview
    assert "The parent" in tree and "The child" not in tree
    assert "The parent" in ready and "The orphan" not in ready

    browser.get("/tags?clear=1&back=/")
    assert "The child" in browser.get("/tickets").text and browser.cookies.get(COOKIE) is None


def test_the_bar_shows_the_chosen_tags_with_a_drop_link_and_the_known_tags(client):
    browser = client(DeclaredBacklog())
    browser.get("/tags?add=p0&back=/")

    page = browser.get("/tree").text

    assert 'href="/tags?drop=p0&back=/tree"' in page
    assert '<option value="auth"></option>' in page
    assert 'form class="addtag" method="get" action="/tags"' in page
    assert '<button type="submit" title="see every view through this tag">see</button>' in page
    assert 'href="/tags?clear=1&back=/tree"' in page

    browser.get("/tags?drop=p0&back=/")
    assert browser.cookies.get(COOKIE) is None


def test_the_ticket_page_is_not_narrowed_but_shows_the_tags(client):
    browser = client(DeclaredBacklog())
    browser.get("/tags?add=auth&back=/")

    page = browser.get("/ticket/pro-01m2bbbbbbbb").text

    assert "<h1>The child</h1>" in page and 'href="/tags?drop=auth' in page


def test_the_way_back_must_be_a_path_on_this_panel(client):
    browser = client(DeclaredBacklog())

    off = browser.get("/tags?add=p0&back=https://evil.example/", follow_redirects=False)
    doubled = browser.get("/tags?add=p0&back=//evil.example", follow_redirects=False)
    none = browser.get("/tags?add=p0", follow_redirects=False)

    assert off.headers["location"] == doubled.headers["location"] == none.headers["location"] == "/"


def test_a_tag_nobody_carries_narrows_every_view_to_nothing(client):
    browser = client(DeclaredBacklog())
    browser.get("/tags?add=nowhere&back=/")

    assert "0 of 0" in browser.get("/tickets").text
    assert "nothing here" in browser.get("/queue/blocked").text
    assert not ticket("x").tags
