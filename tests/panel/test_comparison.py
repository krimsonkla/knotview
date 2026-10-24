"""Two backlogs compared ticket by ticket, without a page."""

from dataclasses import replace

from knotview.panel.comparison import Change, Comparison
from tests.panel.declared import CHILD, CLOSED, ORPHAN, PARENT, ticket

ONLY_HERE = ticket("pro-01m2hhhhhhhh", title="Only here")
ONLY_THERE = ticket("pro-01m2tttttttt", title="Only there")


def _between(here_live=(), here_closed=(), there_live=(), there_closed=()) -> Comparison:
    """The comparison of two declared sides."""
    return Comparison.between(here=(here_live, here_closed), there=(there_live, there_closed))


def test_a_ticket_one_side_holds_is_listed_on_that_side_only():
    compared = _between(
        here_live=(PARENT, ONLY_HERE), there_live=(PARENT,), there_closed=(ONLY_THERE,)
    )

    assert compared.only_here == (ONLY_HERE,)
    assert compared.only_there == (ONLY_THERE,)
    assert compared.alike == (PARENT.id,)


def test_a_ticket_in_both_names_each_field_that_differs_with_both_values():
    there = replace(PARENT, priority=0, title="The parent, renamed", type="feature", tags=("x",))

    compared = _between(here_live=(PARENT,), there_live=(there,))

    assert [pair.id for pair in compared.changed] == [PARENT.id]
    assert compared.changed[0].changes == (
        Change(field="priority", here="1", there="0"),
        Change(field="title", here="The parent", there="The parent, renamed"),
        Change(field="type", here="epic", there="feature"),
    )
    assert not compared.alike and not compared.parted


def test_closed_on_one_side_and_live_on_the_other_is_its_own_group_either_way():
    reopened = replace(CLOSED, status="open")
    finished = replace(CHILD, status="closed")

    compared = _between(
        here_live=(CHILD,), here_closed=(CLOSED,), there_live=(reopened,), there_closed=(finished,)
    )

    assert [pair.id for pair in compared.parted] == [CHILD.id, CLOSED.id]
    assert compared.parted[0].changes == (
        Change(field="status", here="in_progress", there="closed"),
    )
    assert not compared.changed


def test_a_ticket_listed_both_live_and_closed_on_one_side_counts_as_live():
    compared = _between(
        here_live=(ORPHAN,), here_closed=(replace(ORPHAN, status="closed"),), there_live=(ORPHAN,)
    )

    assert compared.alike == (ORPHAN.id,) and not compared.differs


def test_narrowing_keeps_only_the_named_tickets_in_every_group():
    compared = _between(
        here_live=(PARENT, CHILD, ONLY_HERE),
        there_live=(replace(PARENT, priority=0), ONLY_THERE),
        there_closed=(replace(CHILD, status="closed"),),
    ).within({PARENT.id, ONLY_THERE.id})

    assert [pair.id for pair in compared.changed] == [PARENT.id]
    assert compared.only_there == (ONLY_THERE,)
    assert not compared.only_here and not compared.parted and not compared.alike
    assert compared.differs
