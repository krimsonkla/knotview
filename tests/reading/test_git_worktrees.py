"""The worktrees git lists, and the one-directory answer whenever git cannot give them."""

from pathlib import Path

import pytest

from knotview.reading.git_worktrees import GitWorktrees, parsed
from knotview.values.worktree import Worktree


def test_each_record_becomes_a_worktree_in_the_order_git_lists_them(fake_git):
    listed = fake_git().listed()

    assert [(one.name, one.path) for one in listed] == [
        ("main", Path("/repo/knotview")),
        ("feature", Path("/repo/knotview-feature")),
        ("c1d2e3f", Path("/repo/knotview-review")),
    ]


def test_bare_and_prunable_worktrees_are_not_offered():
    output = (
        "worktree /repo/bare.git\0bare\0\0"
        "worktree /repo/knotview\0HEAD aaaa\0branch refs/heads/main\0\0"
        "worktree /repo/gone\0HEAD bbbb\0branch refs/heads/old\0"
        "prunable gitdir file points to non-existent location\0\0"
    )

    assert [one.path for one in parsed(output)] == [Path("/repo/knotview")]


def test_a_record_that_does_not_open_with_its_path_makes_the_whole_listing_unread():
    assert not parsed("HEAD aaaa\0branch refs/heads/main\0\0")
    assert not parsed("worktree\0\0")


@pytest.mark.parametrize("mode", ["refuse", "outside", "junk", "hang"])
def test_a_git_that_cannot_answer_leaves_the_launch_directory_alone(fake_git, tmp_path, mode):
    """An older git refusing -z, a directory that is not a repository, output of another shape,
    and a git that never answers all read the same: one worktree, so no picker."""
    assert fake_git(mode=mode).listed() == (Worktree(path=tmp_path.resolve()),)


def test_a_listing_with_nothing_offered_leaves_the_launch_directory_alone(fake_git, tmp_path):
    assert fake_git(output="worktree /repo/bare.git\0bare\0\0").listed() == (
        Worktree(path=tmp_path.resolve()),
    )


def test_a_missing_git_leaves_the_launch_directory_alone(tmp_path):
    missing = GitWorktrees(repository=tmp_path, git=str(tmp_path / "absent"))

    assert missing.listed() == (Worktree(path=tmp_path.resolve()),)


def test_git_is_only_ever_asked_to_list_worktrees_in_the_resolved_launch_directory(
    fake_git, tmp_path
):
    reader = fake_git()

    reader.listed()

    assert reader.launch == tmp_path.resolve()
    assert (tmp_path / "argv").read_text(encoding="utf-8").split("\0") == [
        "-C",
        str(tmp_path.resolve()),
        "worktree",
        "list",
        "--porcelain",
        "-z",
    ]


def test_a_path_git_prints_that_is_not_utf8_is_left_out_and_the_rest_offered(fake_git):
    output = (
        b"worktree /repo/\xff\0HEAD aaaa\0detached\0\0"
        b"worktree /repo/knotview\0HEAD bbbb\0branch refs/heads/main\0\0"
        b"worktree /repo/knotview-feature\0HEAD cccc\0branch refs/heads/feature\0\0"
    )

    assert [one.name for one in fake_git(output=output).listed()] == ["main", "feature"]


def test_a_path_caught_in_a_symlink_loop_is_left_out(tmp_path):
    loop = tmp_path / "loop"
    loop.symlink_to(loop)
    output = f"worktree {loop}\0HEAD aaaa\0detached\0\0worktree /repo/knotview\0HEAD bbbb\0\0"

    assert [one.path for one in parsed(output)] == [Path("/repo/knotview")]


def test_a_git_that_fails_after_answering_keeps_offering_its_last_listing(fake_git):
    """A wedged or briefly failing git would otherwise drop every tab to the launch directory for
    one render and back again on the next."""
    reader = fake_git()
    answered = reader.listed()

    fake_git(mode="outside")

    assert len(answered) == 3
    assert reader.listed() == answered
