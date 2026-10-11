"""Reading one of a repository's worktrees, chosen in the frame and kept in a cookie."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from knotview.panel.app import _given
from knotview.panel.worktree_choice import cookie_name, encoded
from knotview.values.worktree import Worktree
from tests.panel.declared import PARENT, DeclaredBacklog, RefusingBacklog, ticket

MAIN = Worktree(path=Path("/repo/knotview"), head="a" * 40, branch="refs/heads/main")
FEATURE = Worktree(path=Path("/repo/knotview-feature"), head="b" * 40, branch="refs/heads/feature")
REVIEW = Worktree(path=Path("/repo/knotview-review"), head="c1d2e3f4" + "0" * 32)
AWKWARD = Worktree(path=Path('/repo/my wt, x; "é" 100%+1'), branch="refs/heads/odd")
FEATURE_ONLY = ticket("pro-01m2ffffffff", title="Only on the feature branch")
COOKIE = cookie_name(MAIN.path)


@dataclass
class DeclaredWorktrees:
    """A worktree source over a declared list, counting how often it is asked."""

    worktrees: tuple[Worktree, ...] = (MAIN, FEATURE)
    start: Path = MAIN.path
    calls: int = 0

    @property
    def launch(self) -> Path:
        """Where the panel was started."""
        return self.start

    def listed(self) -> tuple[Worktree, ...]:
        """The declared worktrees, counting the ask."""
        self.calls += 1
        return self.worktrees


@dataclass
class Opener:
    """Backlogs by path, noting every path a reader was made for."""

    held: dict[Path, object] = field(default_factory=dict)
    asked: list[Path] = field(default_factory=list)

    def __call__(self, path: Path) -> object:
        self.asked.append(path)
        return self.held[path]


def _panel(client, *, main=None, feature=None, source=None):
    """A browser over a panel with a main and a feature worktree, plus its source and opener."""
    opener = Opener(
        {
            FEATURE.path: feature
            or DeclaredBacklog(live_value=(FEATURE_ONLY,), digests=["f1"] * 3),
            REVIEW.path: DeclaredBacklog(),
            AWKWARD.path: DeclaredBacklog(live_value=(FEATURE_ONLY,)),
        }
    )
    source = source or DeclaredWorktrees()
    main = main or DeclaredBacklog(digests=["m1"] * 3)
    return client(main, worktrees=source, opened=opener), source, opener


def _marked(page: str) -> list[str]:
    """The labels of every picker entry marked as the one being read."""
    return re.findall(r'<a[^>]*aria-current="true"[^>]*>([^<]*)<', page)


def _choose(browser, worktree: Worktree, back: str = "/tree"):
    """Choose a worktree through the route, as the picker's link does."""
    return browser.get(
        "/worktree", params={"path": str(worktree.path), "back": back}, follow_redirects=False
    )


def test_the_frame_lists_each_worktree_by_name_and_directory_marking_the_one_read(client):
    browser, _, _ = _panel(client)

    page = browser.get("/tree").text

    assert "main · knotview" in page and "feature · knotview-feature" in page
    assert _marked(page) == ["main · knotview"]
    assert 'title="/repo/knotview-feature"' in page


def test_choosing_a_worktree_goes_back_to_the_page_and_every_page_then_reads_it(client):
    browser, _, _ = _panel(client)

    answer = _choose(browser, FEATURE)
    tree = browser.get("/tree").text
    tickets = browser.get("/tickets").text

    assert answer.status_code == 303 and answer.headers["location"] == "/tree"
    assert FEATURE_ONLY.title in tree and PARENT.title not in tree
    assert FEATURE_ONLY.title in tickets
    assert _marked(tickets) == ["feature · knotview-feature"]


def test_a_detached_worktree_is_offered_by_its_short_head(client):
    browser, _, _ = _panel(client, source=DeclaredWorktrees(worktrees=(MAIN, FEATURE, REVIEW)))

    assert "c1d2e3f · knotview-review" in browser.get("/tree").text


def test_a_cookie_naming_an_unlisted_directory_reads_the_launch_directory(client):
    browser, _, opener = _panel(client)

    page = browser.get("/tree", headers={"cookie": f"{COOKIE}={encoded(Path('/elsewhere'))}"})

    assert PARENT.title in page.text
    assert not opener.asked


def test_choosing_an_unlisted_path_clears_the_choice(client):
    browser, _, _ = _panel(client)
    _choose(browser, FEATURE)

    answer = browser.get("/worktree?path=/elsewhere&back=/", follow_redirects=False)

    assert answer.status_code == 303
    assert browser.cookies.get(COOKIE) is None
    assert PARENT.title in browser.get("/tree").text


def test_the_way_back_from_a_choice_must_be_a_path_on_this_panel(client):
    browser, _, _ = _panel(client)

    off = _choose(browser, FEATURE, back="https://elsewhere.example/")
    doubled = _choose(browser, FEATURE, back="//elsewhere.example")
    slanted = _choose(browser, FEATURE, back="/\\elsewhere.example")

    assert off.headers["location"] == doubled.headers["location"] == "/"
    assert slanted.headers["location"] == "/"


def test_the_default_factory_answers_the_one_backlog_for_any_path():
    backlog = DeclaredBacklog()

    assert _given(backlog, Path("/anywhere")) is backlog


def test_a_launch_below_a_worktree_root_reads_that_place_in_the_chosen_worktree(client):
    below = DeclaredWorktrees(start=MAIN.path / "sub")
    browser, _, opener = _panel(client, source=below)
    opener.held[FEATURE.path / "sub"] = DeclaredBacklog(live_value=(FEATURE_ONLY,))

    _choose(browser, FEATURE)

    assert FEATURE_ONLY.title in browser.get("/tree").text
    assert opener.asked == [FEATURE.path / "sub"]


def test_a_chosen_worktree_that_cannot_be_read_still_offers_the_picker(client):
    browser, _, _ = _panel(client, feature=RefusingBacklog())
    _choose(browser, FEATURE)

    page = browser.get("/")

    assert page.status_code == 503 and "no knot project here" in page.text
    assert "main · knotview" in page.text and 'back=/"' in page.text


def test_an_unreadable_launch_directory_still_offers_its_sibling_worktrees(client):
    browser, _, _ = _panel(client, main=RefusingBacklog())

    page = browser.get("/")

    assert page.status_code == 503 and "feature · knotview-feature" in page.text


def test_a_ticket_the_chosen_worktree_lacks_answers_not_found_with_the_picker(client):
    browser, _, _ = _panel(client)

    page = browser.get(
        "/worktree", params={"path": str(FEATURE.path), "back": f"/ticket/{PARENT.id}"}
    )

    assert page.status_code == 404
    assert _marked(page.text) == ["feature · knotview-feature"]


def test_a_launch_directory_inside_a_worktree_marks_that_worktree(client):
    inside, _, _ = _panel(client, source=DeclaredWorktrees(start=MAIN.path / "sub"))
    outside, _, _ = _panel(client, source=DeclaredWorktrees(start=Path("/elsewhere")))

    assert _marked(inside.get("/tree").text) == ["main · knotview"]
    assert _marked(outside.get("/tree").text) == []


def test_a_path_with_spaces_commas_semicolons_quotes_and_accents_can_be_chosen(client):
    browser, _, _ = _panel(client, source=DeclaredWorktrees(worktrees=(MAIN, AWKWARD)))

    _choose(browser, AWKWARD)

    assert FEATURE_ONLY.title in browser.get("/tree").text


def test_a_switch_moves_the_digest_away_from_the_one_the_page_carries(client):
    browser, _, _ = _panel(client)
    carried = re.search(r'data-digest="([^"]+)"', browser.get("/tree").text).group(1)

    _choose(browser, FEATURE)
    answer = browser.get("/digest").text

    assert carried == "m1"
    assert answer != carried and answer.endswith(".f1")


def test_the_digest_never_asks_git(client):
    browser, source, _ = _panel(client)
    browser.get("/tree")
    asked = source.calls

    browser.get("/digest")
    browser.get("/digest")

    assert source.calls == asked


def test_a_restarted_panel_answers_the_launch_digest_before_any_page_lists_worktrees(client):
    browser, source, opener = _panel(client)

    answer = browser.get("/digest", headers={"cookie": f"{COOKIE}={encoded(FEATURE.path)}"})

    assert answer.text == "m1"
    assert source.calls == 0 and not opener.asked


def test_a_removed_worktree_falls_back_to_the_launch_directory_and_leaves_the_picker(client):
    source = DeclaredWorktrees(worktrees=(MAIN, FEATURE, REVIEW))
    browser, _, _ = _panel(client, source=source)
    _choose(browser, FEATURE)

    source.worktrees = (MAIN, REVIEW)
    page = browser.get("/tree").text

    assert PARENT.title in page and "knotview-feature" not in page
    assert _marked(page) == ["main · knotview"]


def test_one_worktree_shows_no_picker(client):
    alone, _, _ = _panel(client, source=DeclaredWorktrees(worktrees=(MAIN,)))

    assert 'class="worktrees"' not in alone.get("/tree").text
    assert 'class="worktrees"' not in client(DeclaredBacklog()).get("/tree").text


def test_a_page_whose_digest_is_refused_renders_without_carrying_one(client):
    browser = client(DeclaredBacklog())

    first = browser.get("/tree").text
    second = browser.get("/tree").text

    assert 'data-digest="d1"' in first
    assert "data-digest" not in second and PARENT.title in second
