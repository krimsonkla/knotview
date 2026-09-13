"""One read of a backlog, taken together."""

import pytest

from knotview.reading.backlog import Backlog
from knotview.reading.snapshot import Snapshot
from tests.panel.declared import CHILD, CLOSED, ORPHAN, PARENT, DeclaredBacklog


def test_a_snapshot_carries_every_part_of_one_read():
    backlog = DeclaredBacklog(integrity_value=("a line",))

    taken = Snapshot.read(backlog)

    assert taken.project is backlog.project_value
    assert taken.live == (PARENT, CHILD, ORPHAN)
    assert taken.closed == (CLOSED,)
    assert (taken.ready, taken.blocked) == ((PARENT, ORPHAN), (CHILD,))
    assert taken.integrity == ("a line",)


def test_the_declared_backlog_satisfies_the_port():
    assert isinstance(DeclaredBacklog(), Backlog)


@pytest.mark.parametrize(
    "name", ["project", "live", "closed", "ready", "blocked", "integrity", "digest"]
)
def test_the_port_itself_answers_nothing(name: str):
    """The protocol's bodies are refusals, not defaults, so a class that inherits one by mistake
    fails at the call rather than answering an empty backlog."""
    with pytest.raises(NotImplementedError):
        getattr(Backlog, name)(object())


def test_the_port_itself_answers_no_ticket_either():
    with pytest.raises(NotImplementedError):
        Backlog.ticket(object(), "x")
