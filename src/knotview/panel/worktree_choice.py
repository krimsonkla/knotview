"""Which worktree a reader has chosen, and how the choice travels in their browser."""

import hashlib
from pathlib import Path
from urllib.parse import quote, unquote

from knotview.values.worktree import Worktree

# The cookie's name before its suffix. A cookie because the choice is the reader's, like their
# tags: it lives in their browser and is never written anywhere the panel reads tickets from.
PREFIX = "knotview_worktree_"


def cookie_name(launch: Path) -> str:
    """The cookie for one panel's choice, named for the directory the panel was started in.

    A browser sends a host's cookies to every port on it, so two panels over two repositories would
    otherwise overwrite each other's choice. The suffix is a digest of the resolved launch
    directory, which is known whether or not git answers.
    """
    return PREFIX + hashlib.sha256(str(launch.resolve()).encode("utf-8")).hexdigest()[:12]


def encoded(path: Path) -> str:
    """A path as a cookie carries it, with every character outside the unreserved set escaped.

    A worktree can live under a path with spaces, commas, semicolons, quotes or any script, and a
    cookie value cannot hold most of those as they are.
    """
    return quote(str(path), safe="")


def named(text: str, among: tuple[Worktree, ...]) -> Worktree | None:
    """The listed worktree a path names, after resolving, or nothing.

    Never trusted on its own: the path picks the directory knot is run in, and anyone can edit a
    cookie or a link. A blank names nothing rather than the working directory, and a path that
    cannot be a path (it holds a NUL, or loops) names nothing rather than failing the page.
    """
    if not text:
        return None
    try:
        wanted = Path(text).resolve()
    except (ValueError, OSError, RuntimeError):
        # A NUL in the text, or a symlink loop (RuntimeError on Python 3.12, OSError later).
        return None
    return next((one for one in among if one.path == wanted), None)


def chosen(held: str | None, among: tuple[Worktree, ...]) -> Worktree | None:
    """The listed worktree a cookie names, or nothing for a cookie that names no listed one."""
    return named(unquote(held or ""), among)


def containing(launch: Path, among: tuple[Worktree, ...]) -> Worktree | None:
    """The deepest listed worktree the launch directory is in, or nothing if it is in none.

    A panel started in a subdirectory of a checkout is reading that checkout, so that is the entry
    the picker marks; a worktree nested inside another wins, being the nearer one.
    """
    holding = [one for one in among if launch.is_relative_to(one.path)]
    return max(holding, key=lambda one: len(one.path.parts), default=None)
