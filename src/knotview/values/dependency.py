"""One ticket's dependencies, as the tree knot draws under it."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Dependency:
    """A node of the dependency tree: a ticket and what it waits on, recursively.

    Two flags carry the shapes knot's tree can take besides a plain node. A missing node names a
    dependency no ticket has, which is a dangling reference the integrity check also reports. A
    node seen before is one the tree already drew higher up: knot stops there rather than drawing
    it twice, so a diamond shows once and a cycle cannot recurse.
    """

    id: str
    title: str
    status: str
    missing: bool = False
    seen_before: bool = False
    deps: tuple["Dependency", ...] = ()

    def blocks(self, terminal: tuple[str, ...]) -> bool:
        """Whether this node still stands in the way: present, and not in a terminal status.

        The terminal statuses are the project's own, never assumed to be spelled `closed`.
        """
        return not self.missing and self.status not in terminal
