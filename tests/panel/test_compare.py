"""The page comparing the chosen worktree's backlog with another worktree's."""

import re
from dataclasses import replace
from pathlib import Path
from urllib.parse import quote

from tests.panel.declared import (
    CHILD,
    CLOSED,
    ORPHAN,
    PARENT,
    DeclaredBacklog,
    RefusingBacklog,
)
from tests.panel.test_worktrees import (
    COOKIE,
    FEATURE,
    FEATURE_ONLY,
    MAIN,
    REVIEW,
    DeclaredWorktrees,
    Opener,
)
from knotview.panel.worktree_choice import encoded

# The feature branch's copy of the backlog: one new ticket, the parent re-prioritised, the child
# finished, the orphan untouched and the closed ticket never there.
FEATURE_BACKLOG = (
    (FEATURE_ONLY, replace(PARENT, priority=0), ORPHAN),
    (replace(CHILD, status="closed"),),
)


def _panel(client, *, main=None, feature=None, source=None):
    """A browser over a panel with main and feature worktrees, plus the opener it reads through."""
    live, closed = FEATURE_BACKLOG
    opener = Opener(
        {
            FEATURE.path: feature
            or DeclaredBacklog(live_value=live, closed_value=closed, digests=["f1"] * 9),
            REVIEW.path: DeclaredBacklog(digests=["r1"] * 9),
        }
    )
    main = main or DeclaredBacklog(digests=["m1"] * 9)
    browser = client(main, worktrees=source or DeclaredWorktrees(), opened=opener)
    return browser, opener


def _with(worktree) -> str:
    """The comparison with one worktree, as the panel links it."""
    return "/compare?with=" + quote(str(worktree.path), safe="")


def _section(page: str, heading: str) -> str:
    """The part of a page from one group's heading to the next heading."""
    return page.split(heading, 1)[1].split("<h2", 1)[0]


def test_the_header_links_to_a_comparison_with_the_first_other_worktree(client):
    browser, _ = _panel(client)

    page = browser.get("/tree").text

    assert 'href="/compare?with=%2Frepo%2Fknotview-feature"' in page
    assert 'aria-label="Compare worktrees"' in page


def test_reading_another_worktree_offers_the_launch_directory_to_compare_with(client):
    browser, _ = _panel(client)

    page = browser.get("/tree", headers={"cookie": f"{COOKIE}={encoded(FEATURE.path)}"}).text

    assert 'href="/compare?with=%2Frepo%2Fknotview"' in page


def test_one_worktree_offers_no_comparison_and_the_page_says_there_is_none(client):
    browser, _ = _panel(client, source=DeclaredWorktrees(worktrees=(MAIN,)))

    assert "Compare worktrees" not in browser.get("/tree").text
    assert "nothing to compare" in browser.get(_with(FEATURE)).text


def test_the_comparison_lists_each_side_s_own_tickets_and_what_changed(client):
    browser, opener = _panel(client)

    page = browser.get(_with(FEATURE)).text
    here = _section(page, "only in main · knotview <span")
    there = _section(page, "only in feature · knotview-feature <span")
    parted = _section(page, "closed on one side, live on the other")
    changed = _section(page, ">changed <span")

    assert CLOSED.title in here and FEATURE_ONLY.title in there
    assert CHILD.title in parted and "in_progress" in parted and ">closed</span>" in parted
    assert PARENT.title in changed and ">1</span>" in changed and ">0</span>" in changed
    assert '<span class="kv-count">1</span> the same' in page
    assert ORPHAN.title not in page
    assert opener.asked == [FEATURE.path]


def test_a_ticket_only_the_other_side_holds_has_no_link_here(client):
    browser, _ = _panel(client)

    page = browser.get(_with(FEATURE)).text

    assert f'<span class="title">{FEATURE_ONLY.title}</span>' in page
    assert f"/ticket/{FEATURE_ONLY.id}" not in page
    assert f'href="/ticket/{CLOSED.id}"' in page


def test_two_identical_backlogs_say_so(client):
    browser, _ = _panel(client, feature=DeclaredBacklog(digests=["f1"] * 9))

    page = browser.get(_with(FEATURE)).text

    assert "the same on both sides" in page
    assert '<span class="kv-count">4</span> the same' in page


def test_without_another_worktree_named_the_page_offers_the_choice_and_reads_nothing(client):
    browser, opener = _panel(client)

    page = browser.get("/compare").text

    assert "choose a worktree" in page and "That is not another worktree" not in page
    assert (
        '<form class="kv-worktrees kv-compare-pick" method="get" action="/compare" data-auto>'
        in page
    )
    assert "Compare with feature · knotview-feature" in page
    assert re.findall(r'<option\s+value="(/[^"]*)"', page.split("compare-with", 1)[1]) == [
        str(FEATURE.path)
    ]
    assert not opener.asked


def test_an_unlisted_or_unreadable_path_reads_nothing_and_shows_the_choice(client):
    browser, opener = _panel(client)

    elsewhere = browser.get("/compare?with=/elsewhere").text
    nul = browser.get("/compare?with=/repo/%00").text

    assert "That is not another worktree git lists now" in elsewhere
    assert "That is not another worktree git lists now" in nul
    assert not opener.asked


def test_the_worktree_being_read_is_not_one_to_compare_with(client):
    browser, opener = _panel(client)

    page = browser.get(_with(MAIN)).text

    assert "That is not another worktree git lists now" in page
    assert not opener.asked


def test_a_relative_spelling_of_a_listed_worktree_compares_with_it(client):
    browser, _ = _panel(client)

    page = browser.get("/compare?with=/repo/knotview/../knotview-feature/").text

    assert FEATURE_ONLY.title in page


def test_another_worktree_that_cannot_be_read_says_so_and_keeps_the_choice(client):
    browser, _ = _panel(client, feature=RefusingBacklog())

    page = browser.get(_with(FEATURE))

    assert page.status_code == 503
    assert "feature · knotview-feature could not be read" in page.text
    assert "no knot project here" in page.text and "run knot init, or point elsewhere" in page.text
    assert 'data-digest="m1~-"' in page.text
    assert re.search(r"<option\s+value=\"/repo/knotview-feature\"[^>]*selected", page.text)


def test_the_comparison_follows_both_sides(client):
    browser, _ = _panel(client)

    page = browser.get(_with(FEATURE)).text
    carried = re.search(r'data-digest="([^"]+)"', page).group(1)
    followed = re.search(r'data-follow="([^"]+)"', page).group(1)

    assert carried.startswith("m1~") and carried.endswith(".f1")
    assert followed == "/digest?with=%2Frepo%2Fknotview-feature"
    assert browser.get(followed).text == carried


def test_the_comparison_s_digest_never_asks_git_and_ignores_an_unlisted_side(client):
    source = DeclaredWorktrees()
    browser, opener = _panel(client, source=source)
    browser.get("/tree")
    asked = source.calls

    answer = browser.get("/digest?with=/elsewhere").text

    assert answer == "m1"
    assert source.calls == asked and not opener.asked


def test_other_pages_follow_only_the_chosen_worktree(client):
    browser, _ = _panel(client)

    assert "data-follow" not in browser.get("/tree").text


def test_a_comparison_whose_own_digest_is_refused_carries_none(client):
    browser, _ = _panel(client, main=DeclaredBacklog(digests=[]))

    page = browser.get(_with(FEATURE)).text

    assert "data-digest" not in page and FEATURE_ONLY.title in page


def test_pinned_tags_narrow_the_comparison_by_either_side_s_copy(client):
    browser, _ = _panel(client)
    browser.get("/tags?add=auth&back=/")

    page = browser.get(_with(FEATURE)).text

    assert PARENT.title in page
    assert FEATURE_ONLY.title not in page and CLOSED.title not in page


def test_a_launch_outside_every_worktree_compares_from_the_launch_directory(client):
    source = DeclaredWorktrees(start=Path("/elsewhere"))
    browser, opener = _panel(client, source=source)

    page = browser.get(_with(FEATURE)).text

    assert "only in the launch directory" in page and FEATURE_ONLY.title in page
    assert opener.asked == [FEATURE.path]


def test_the_compare_link_is_marked_on_its_own_page(client):
    browser, _ = _panel(client)

    page = browser.get("/compare").text

    assert re.search(r'class="kv-icon kv-compare-link"[^>]*aria-current="page"', page)
