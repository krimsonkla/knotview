"""What the command remembers about a project: where it is, and which port it gets."""

from dataclasses import dataclass
from pathlib import Path

from knotview.values.unknown_project import UnknownProject

# The ports a socket can bind. Zero is left out: it means an ephemeral port, and a saved default
# that changed on every run would be a default nobody could bookmark.
LOWEST_PORT, HIGHEST_PORT = 1, 65535


@dataclass(frozen=True, kw_only=True)
class SavedProject:
    """A repository and a port, which are the two things the command otherwise has to be told.

    Both are facts about this machine rather than about the project: which port is free here, and
    where this checkout happens to live. That is why they are saved beside the person's own
    configuration rather than in the project, where they would travel to a machine on which the port
    is taken and the path is wrong.
    """

    repository: Path
    port: int

    def __post_init__(self) -> None:
        if not LOWEST_PORT <= self.port <= HIGHEST_PORT:
            raise UnknownProject(
                f"{self.port} is not a port",
                advice=f"choose a port between {LOWEST_PORT} and {HIGHEST_PORT}",
            )
