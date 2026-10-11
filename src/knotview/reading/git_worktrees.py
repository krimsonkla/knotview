"""The repository's worktrees, read by asking git to list them."""

import subprocess
from pathlib import Path

from knotview.reading.knot_command import PATIENCE
from knotview.values.worktree import Worktree

# The command, named for the same reason knot's is: the second and last place this panel reaches
# outside itself is one constant somebody can see.
GIT = "git"

# The one thing git is ever asked. It lists and changes nothing, and -z ends every field with a
# NUL, so a path holding a space or a newline arrives whole. It needs git 2.36 or later; an older
# git refuses the option, which reads the same as git not answering.
LISTING = ("worktree", "list", "--porcelain", "-z")

# The labels git puts on a worktree no backlog can be read from: a bare repository has no checkout,
# and a prunable worktree's directory is gone.
UNREADABLE = ("bare", "prunable")

# What a byte that is not UTF-8 decodes to. A path holding one cannot be named faithfully, so the
# worktree it belongs to is left out rather than offered under a name that opens nothing.
UNDECODABLE = "\ufffd"


class GitWorktrees:
    """The worktrees of the repository the panel was started in, or that directory alone.

    Never a refusal. Worktrees are a convenience on top of a panel that already works over one
    directory, so git missing, too old, pointed at something that is not a repository, wedged, or
    answering in a shape this does not know all mean one thing: there is one worktree, the one the
    panel was started in, and the panel looks as it did before it knew about worktrees.

    Once git has answered, a later failure offers that last answer instead. A git that is briefly
    wedged would otherwise drop every open tab to the launch directory for one render and back
    again on the next. The answer is one tuple replaced whole, so threads reading it never see
    half of one.
    """

    def __init__(self, *, repository: Path, git: str = GIT, patience: int = PATIENCE) -> None:
        self._launch = repository.resolve()
        self._git = git
        self._patience = patience
        self._answered: tuple[Worktree, ...] = ()

    @property
    def launch(self) -> Path:
        """The directory the panel was started in, resolved, which answers when git cannot."""
        return self._launch

    def listed(self) -> tuple[Worktree, ...]:
        """Every worktree git offers a backlog in, in git's order, else git's last answer, else the
        launch directory alone."""
        try:
            answer = subprocess.run(
                self._spoken(),
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=self._patience,
            )
        except (OSError, subprocess.TimeoutExpired):
            return self._answered or self._alone()
        found = parsed(answer.stdout) if answer.returncode == 0 else ()
        if found:
            self._answered = found
        return self._answered or self._alone()

    def _spoken(self) -> list[str]:
        """The argument list git is handed: the repository by -C, then the one listing."""
        return [self._git, "-C", str(self._launch), *LISTING]

    def _alone(self) -> tuple[Worktree, ...]:
        """The launch directory as the only worktree."""
        return (Worktree(path=self._launch),)


def parsed(output: str) -> tuple[Worktree, ...]:
    """git's NUL-separated records as worktrees, or nothing if any record is not one.

    A record is a run of "label value" fields ended by an empty field. One that does not open with
    its worktree's path is a shape this was not written for, and guessing at the rest could offer
    the reader a directory git never named.
    """
    found: list[Worktree] = []
    for record in output.split("\0\0"):
        fields = [one for one in record.split("\0") if one]
        if not fields:
            continue
        label, _, path = fields[0].partition(" ")
        if label != "worktree" or not path:
            return ()
        held = dict(one.partition(" ")[::2] for one in fields[1:])
        if any(mark in held for mark in UNREADABLE) or UNDECODABLE in path:
            continue
        try:
            resolved = Path(path).resolve()
        except (OSError, RuntimeError):
            # A symlink loop: Python 3.12 raises RuntimeError for it, later versions OSError.
            continue
        found.append(Worktree(path=resolved, head=held.get("HEAD", ""), branch=held.get("branch")))
    return tuple(found)
