"""How a worktree is named in the picker."""

from pathlib import Path

from knotview.values.worktree import Worktree


def test_a_worktree_on_a_branch_is_named_by_the_branch_without_its_ref_prefix():
    one = Worktree(path=Path("/repo/knotview"), head="a" * 40, branch="refs/heads/jr/feature")

    assert one.name == "jr/feature"
    assert one.label == "jr/feature · knotview"


def test_a_detached_worktree_is_named_by_the_first_seven_characters_of_its_head():
    one = Worktree(path=Path("/repo/review"), head="c1d2e3f4a5b6")

    assert one.name == "c1d2e3f"
    assert one.label == "c1d2e3f · review"
