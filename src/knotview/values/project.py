"""What a knot project says about itself, which is what makes this panel dynamic."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Project:
    """The configuration the panel is shaped by, read from the project rather than assumed.

    Every list here is the project's own. A panel with its own idea of which types exist is a panel
    that is wrong about the next repository it is pointed at: knot lets a project declare its types,
    its statuses, which status is active and which are terminal, its modes and its priority range,
    and all of that drives the navigation rather than decorating it.

    The active and terminal statuses matter more than they look. They are what lets the panel say
    "in progress" and "closed" without knowing those words: one project's active status may be
    `doing` and another's `in_progress`, and a panel that hardcoded either would mislabel the other.
    """

    name: str
    prefix: str
    knot_version: str
    types: tuple[str, ...]
    statuses: tuple[str, ...]
    active_status: str
    terminal_statuses: tuple[str, ...]
    modes: tuple[str, ...]
    priority_range: tuple[int, int]
    tickets_path: str
    live_count: int
    archive_count: int

    @property
    def open_statuses(self) -> tuple[str, ...]:
        """Every status that is not terminal, in the order the project declared them."""
        return tuple(status for status in self.statuses if status not in self.terminal_statuses)

    @property
    def priorities(self) -> tuple[int, ...]:
        """Every priority the project permits, lowest number first, which is highest first."""
        lowest, highest = self.priority_range
        return tuple(range(lowest, highest + 1))

    def is_terminal(self, status: str) -> bool:
        """Whether that status means a ticket is done with, whatever the project calls it."""
        return status in self.terminal_statuses
