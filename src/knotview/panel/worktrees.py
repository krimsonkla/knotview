"""Which backlog a request reads: the chosen worktree's, or the launch directory's."""

import hashlib
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from knotview.panel.worktree_choice import chosen, containing, cookie_name, named
from knotview.reading.backlog import Backlog
from knotview.values.worktree import Worktree


class WorktreeSource(Protocol):
    """Where worktrees come from: git for the command, a declared list for a test."""

    @property
    def launch(self) -> Path:
        """The directory the panel was started in, resolved."""
        raise NotImplementedError

    def listed(self) -> tuple[Worktree, ...]:
        """Every worktree offered, or the launch directory alone; never empty, never a refusal."""
        raise NotImplementedError


class Alone:
    """One worktree and nothing to ask: the panel built over one backlog, as the tests build it."""

    def __init__(self, launch: Path) -> None:
        self._launch = launch.resolve()

    @property
    def launch(self) -> Path:
        """The one directory."""
        return self._launch

    def listed(self) -> tuple[Worktree, ...]:
        """The one directory as the only worktree."""
        return (Worktree(path=self._launch),)


class Backlogs:
    """One backlog reader per worktree, and which one a request's cookie picks.

    Page handlers run in the thread pool, so the readers and the last listing are shared between
    threads. Both sit behind one lock: a reader is made at most once per path, and a listing is
    replaced whole. Pages refresh the listing, since a page render already starts processes. The
    digest only reads it, because every open tab asks for the digest about once a second, and a git
    process per tick per tab is the cost the digest exists to avoid.
    """

    def __init__(
        self,
        *,
        launch: Backlog,
        source: WorktreeSource,
        opened: Callable[[Path], Backlog],
    ) -> None:
        self._source = source
        self._opened = opened
        self._lock = threading.Lock()
        self._readers: dict[Path, Backlog] = {source.launch: launch}
        self._listed: tuple[Worktree, ...] = ()
        self.cookie = cookie_name(source.launch)

    @property
    def launch(self) -> Path:
        """The directory the panel was started in, which every unmatched choice falls back to."""
        return self._source.launch

    def refreshed(self) -> tuple[Worktree, ...]:
        """git's list now, kept for the digest to check cookies against."""
        listed = self._source.listed()
        with self._lock:
            self._listed = listed
        return listed

    def known(self) -> tuple[Worktree, ...]:
        """The list the last page render saw, or nothing before the first render, which leaves a
        restarted panel's digest reading the launch directory until a page lists again."""
        with self._lock:
            return self._listed

    def reading(self, held: str | None, among: tuple[Worktree, ...]) -> tuple[Path, Backlog]:
        """The directory a request reads, and its backlog: the chosen worktree, else the launch.

        A panel started below a worktree's root reads the same place below the chosen worktree's
        root, since a knot project kept in a subdirectory is in that subdirectory in every
        checkout. Choosing the worktree the panel was started in reads the launch directory.
        """
        picked = chosen(held, among)
        if not picked:
            return self.launch, self._reader(self.launch)
        path = self._within(picked, among)
        return path, self._reader(path)

    def beside(
        self, asked: str, held: str | None, among: tuple[Worktree, ...]
    ) -> tuple[Worktree, Path, Backlog] | None:
        """The other worktree a comparison names, where it is read, and its backlog; or nothing.

        The name comes from a link, so it is matched against git's list like the cookie is, and
        anything unlisted reads nothing. The worktree being read is not one of the others: a
        backlog compared with itself has nothing to say. The reader is the same one the pages use
        when that worktree is chosen, so a comparison starts no reader of its own.
        """
        reading = self.marked(held, among)
        picked = named(asked, tuple(one for one in among if one.path != reading))
        if not picked:
            return None
        path = self._within(picked, among)
        return picked, path, self._reader(path)

    def counterpart(self, held: str | None, among: tuple[Worktree, ...]) -> Worktree | None:
        """The worktree a comparison offers first: the launch's when another is being read, else
        the first other one git lists, which is the main worktree unless that is the one read."""
        reading = self.marked(held, among)
        home = containing(self.launch, among)
        if home and home.path != reading:
            return home
        return next((one for one in among if one.path != reading), None)

    def _within(self, picked: Worktree, among: tuple[Worktree, ...]) -> Path:
        """Where a worktree's backlog is read: the launch directory's place below its root."""
        home = containing(self.launch, among)
        return picked.path / self.launch.relative_to(home.path) if home else picked.path

    def marked(self, held: str | None, among: tuple[Worktree, ...]) -> Path | None:
        """The worktree the picker marks: the chosen one, else the one holding the launch."""
        picked = chosen(held, among) or containing(self.launch, among)
        return picked.path if picked else None

    def stamped(self, path: Path, digest: str) -> str:
        """A backlog's digest, told apart by the worktree it was read in.

        The launch directory's digest is the backlog's own, so a panel with one worktree answers
        exactly what it answered before. Any other worktree's is prefixed with a digest of its
        path, so switching moves the value every open tab compares against.
        """
        if path == self.launch:
            return digest
        where = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:8]
        return f"{where}.{digest}"

    def _reader(self, path: Path) -> Backlog:
        """The reader for one path, made on first use under the lock, so only once."""
        with self._lock:
            if path not in self._readers:
                self._readers[path] = self._opened(path)
            return self._readers[path]
