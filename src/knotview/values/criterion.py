"""One acceptance criterion, and whether it is ticked."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Criterion:
    """A criterion and its state, which together are how a ticket's progress is read.

    Counting ticked criteria is the only progress figure in this panel that is not a guess. A
    percentage over subtasks assumes every subtask is equal; a criterion is a sentence somebody
    wrote and either met or did not.
    """

    title: str
    done: bool
