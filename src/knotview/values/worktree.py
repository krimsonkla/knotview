"""One working tree of a repository, as git lists it."""

from dataclasses import dataclass
from pathlib import Path

# git names a branch by its full ref; a reader knows it by the part after this.
BRANCHES = "refs/heads/"

# How much of a detached head names it, which is git's own short form.
SHORT_HEAD = 7


@dataclass(frozen=True, kw_only=True)
class Worktree:
    """A checkout of the repository: where it is, and what it has checked out.

    Each one holds its own copy of the backlog, because knot keeps tickets inside the checkout.
    The path is resolved by whoever makes one, so two spellings of one directory are one worktree.
    """

    path: Path
    head: str = ""
    branch: str | None = None

    @property
    def name(self) -> str:
        """The branch without its ref prefix, or the head's short form when nothing is checked out
        by name."""
        if self.branch:
            return self.branch.removeprefix(BRANCHES)
        return self.head[:SHORT_HEAD]

    @property
    def label(self) -> str:
        """What the picker shows. Both halves, since two worktrees can share either one."""
        return f"{self.name} · {self.path.name}"
