"""What a ticket derives from what it holds."""

from knotview.values.reference import Reference
from tests.panel.declared import CHILD, PARENT, PROJECT, ticket


def test_criteria_are_counted_and_the_unmet_ones_named():
    assert (PARENT.met, PARENT.criteria) == (1, 2)
    assert [one.title for one in PARENT.unmet] == ["second thing"]
    assert (CHILD.met, CHILD.criteria, CHILD.unmet) == (0, 0, ())


def test_only_blockers_outside_the_projects_terminal_statuses_are_open():
    """A missing blocker has no status: nothing can close it, so it does not count as blocking."""
    assert not CHILD.open_blockers(PROJECT.terminal_statuses)
    assert [one.id for one in CHILD.blockers if one.missing] == ["pro-01m2zzzzzzzz"]


def test_the_terminal_statuses_are_the_projects_own_not_the_word_closed():
    """One project closes with `done`; its finished blocker must not count as open, and a
    blocker that happens to be called `closed` there is still in the way."""
    held = ticket(
        "x",
        blockers=(
            Reference(id="a", title="Finished", status="done"),
            Reference(id="b", title="Oddly named", status="closed"),
        ),
    )

    assert [one.id for one in held.open_blockers(("done",))] == ["b"]


def test_the_notes_are_named_and_kept_out_of_the_narrative():
    assert PARENT.notes == "A note."
    assert PARENT.narrative() == (("", "Text before any heading."), ("description", "What for."))
    assert ticket("x").notes is None


def test_the_notes_split_on_knots_instants_newest_first():
    held = ticket(
        "x",
        sections={
            "notes": "**2026-09-12T06:44:01.672814Z**\n\nFirst said.\n\n"
            "**2026-09-12T07:42:11.438463Z**\n\nThen this, over\ntwo lines."
        },
    )

    entries = held.timeline()

    assert [(n.at, n.text) for n in entries] == [
        ("2026-09-12T07:42:11.438463Z", "Then this, over\ntwo lines."),
        ("2026-09-12T06:44:01.672814Z", "First said."),
    ]


def test_a_note_without_an_instant_keeps_its_place_and_no_notes_is_nothing():
    held = ticket("x", sections={"notes": "By hand.\n\n**2026-09-13T00:00:00Z**\n\nStamped."})

    assert [(n.at, n.text) for n in held.timeline()] == [
        ("2026-09-13T00:00:00Z", "Stamped."),
        (None, "By hand."),
    ]
    assert not ticket("y").timeline()
