"""Which worktree a cookie picks, and the readers kept for each."""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from knotview.panel.worktree_choice import (
    PREFIX,
    chosen,
    containing,
    cookie_name,
    encoded,
    named,
)
from knotview.panel.worktrees import Alone, Backlogs, WorktreeSource
from knotview.values.worktree import Worktree
from tests.panel.declared import DeclaredBacklog

MAIN = Worktree(path=Path("/repo/knotview"), branch="refs/heads/main")
NESTED = Worktree(path=Path("/repo/knotview/nested"), branch="refs/heads/nested")
AWKWARD = Worktree(path=Path('/repo/my wt, x; "é" 100%+1'), branch="refs/heads/odd")
LISTED = (MAIN, NESTED, AWKWARD)


class Listed:  # pylint: disable=too-few-public-methods
    """A worktree source over LISTED, launched in the main worktree."""

    launch = MAIN.path

    def listed(self) -> tuple[Worktree, ...]:
        """The declared worktrees."""
        return LISTED


def _unused(path: Path) -> DeclaredBacklog:
    """A factory for tests that never make a reader for a new path."""
    raise AssertionError(f"no reader should be made for {path}")


def test_two_launch_directories_get_two_cookie_names_under_one_prefix():
    one, other = cookie_name(Path("/repo/a")), cookie_name(Path("/repo/b"))

    assert one != other
    assert one.startswith(PREFIX) and other.startswith(PREFIX)


def test_any_path_survives_the_cookie_and_picks_its_worktree():
    held = encoded(AWKWARD.path)

    assert all(mark not in held for mark in ' ,;"')
    assert chosen(held, LISTED) == AWKWARD


def test_a_cookie_or_path_that_names_no_listed_worktree_picks_nothing():
    assert chosen(encoded(Path("/elsewhere")), LISTED) is None
    assert chosen(None, LISTED) is None
    assert chosen("", LISTED) is None
    assert chosen("%00", LISTED) is None
    assert named("", LISTED) is None


def test_a_typed_path_is_matched_after_resolving():
    assert named("/repo/knotview/nested/..", LISTED) == MAIN


def test_a_path_caught_in_a_symlink_loop_names_nothing(tmp_path):
    loop = tmp_path / "loop"
    loop.symlink_to(loop)

    assert named(str(loop), LISTED) is None


def test_the_launch_directory_belongs_to_the_deepest_worktree_that_holds_it():
    assert containing(Path("/repo/knotview/nested/src"), LISTED) == NESTED
    assert containing(Path("/repo/knotview/docs"), LISTED) == MAIN
    assert containing(Path("/elsewhere"), LISTED) is None


def test_a_request_reads_the_chosen_worktree_or_else_the_launch_directory():
    launch, nested = DeclaredBacklog(), DeclaredBacklog()
    backlogs = Backlogs(launch=launch, source=Listed(), opened=lambda path: nested)

    read_nested = backlogs.reading(encoded(NESTED.path), LISTED)
    read_elsewhere = backlogs.reading(encoded(Path("/elsewhere")), LISTED)

    assert read_nested[0] == NESTED.path and read_nested[1] is nested
    assert read_elsewhere[0] == MAIN.path and read_elsewhere[1] is launch
    assert backlogs.marked(None, LISTED) == MAIN.path
    assert backlogs.marked(encoded(NESTED.path), LISTED) == NESTED.path


def test_a_launch_below_a_worktree_root_reads_the_same_place_in_the_chosen_worktree():
    other = Worktree(path=Path("/repo/other"), branch="refs/heads/other")
    made: list[Path] = []

    class Below:  # pylint: disable=too-few-public-methods
        """Launched in a subdirectory of the main worktree."""

        launch = MAIN.path / "tools" / "board"

        def listed(self) -> tuple[Worktree, ...]:
            """Main and one other."""
            return (MAIN, other)

    backlogs = Backlogs(
        launch=DeclaredBacklog(),
        source=Below(),
        opened=lambda path: made.append(path) or DeclaredBacklog(),
    )

    assert backlogs.reading(encoded(other.path), (MAIN, other))[0] == other.path / "tools" / "board"
    assert backlogs.reading(encoded(MAIN.path), (MAIN, other))[0] == Below.launch
    assert backlogs.reading(encoded(other.path), (other,))[0] == other.path
    assert made == [other.path / "tools" / "board", other.path]


def test_nothing_is_marked_when_the_launch_directory_is_in_no_listed_worktree():
    backlogs = Backlogs(launch=DeclaredBacklog(), source=Alone(Path("/elsewhere")), opened=_unused)

    assert backlogs.marked(None, LISTED) is None


def test_the_digest_sees_no_listing_until_a_page_has_refreshed_it():
    backlogs = Backlogs(launch=DeclaredBacklog(), source=Listed(), opened=_unused)

    assert not backlogs.known()
    assert backlogs.refreshed() == LISTED
    assert backlogs.known() == LISTED


def test_the_launch_digest_is_unchanged_and_any_other_worktree_s_is_told_apart():
    backlogs = Backlogs(launch=DeclaredBacklog(), source=Listed(), opened=_unused)

    assert backlogs.stamped(MAIN.path, "d1") == "d1"
    assert backlogs.stamped(NESTED.path, "d1").endswith(".d1")
    assert backlogs.stamped(NESTED.path, "d1") != backlogs.stamped(AWKWARD.path, "d1")


def test_concurrent_first_reads_of_one_worktree_make_exactly_one_reader():
    made: list[Path] = []

    def opened(path: Path) -> DeclaredBacklog:
        made.append(path)
        time.sleep(0.01)
        return DeclaredBacklog()

    backlogs = Backlogs(launch=DeclaredBacklog(), source=Listed(), opened=opened)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: backlogs.reading(encoded(NESTED.path), LISTED), range(16)))

    assert made == [NESTED.path]


def test_the_worktree_source_port_itself_answers_nothing():
    """Refusals, not defaults, as the Backlog port's are."""
    with pytest.raises(NotImplementedError):
        WorktreeSource.listed(object())
    with pytest.raises(NotImplementedError):
        WorktreeSource.launch.fget(object())


def test_alone_offers_its_resolved_launch_directory_and_nothing_else(tmp_path):
    alone = Alone(tmp_path / ".")

    assert alone.launch == tmp_path.resolve()
    assert alone.listed() == (Worktree(path=tmp_path.resolve()),)
