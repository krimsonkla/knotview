"""What a ticket derives from what it holds."""

from tests.panel.declared import CHILD, PARENT, ticket


def test_criteria_are_counted_and_the_unmet_ones_named():
    assert (PARENT.met, PARENT.criteria) == (1, 2)
    assert [one.title for one in PARENT.unmet] == ["second thing"]
    assert (CHILD.met, CHILD.criteria, CHILD.unmet) == (0, 0, ())


def test_only_blockers_that_are_not_closed_are_open_and_a_missing_one_counts_as_open():
    """A missing blocker arrives with no status. Counting it as open is the current behaviour and
    is asserted as such; showing it as missing is a follow-up."""
    assert [one.id for one in CHILD.open_blockers] == ["pro-01m2zzzzzzzz"]


def test_the_notes_are_named_and_kept_out_of_the_narrative():
    assert PARENT.notes == "A note."
    assert PARENT.narrative() == (("", "Text before any heading."), ("description", "What for."))
    assert ticket("x").notes is None
