"""What a project derives from its declared values."""

from dataclasses import replace

from knotview.values.document import Document
from tests.panel.declared import PROJECT, ticket


def test_open_statuses_are_the_declared_ones_that_are_not_terminal():
    assert PROJECT.open_statuses == ("open", "in_progress")


def test_priorities_run_the_declared_range_highest_first():
    assert PROJECT.priorities == (0, 1, 2, 3, 4)


# Documents whose id, created, title and alphabetical type orders all disagree, so no ordering
# but the declared one can pass by accident.
SHUFFLED = (
    Document(id="x-d1", ticket="x", title="B", type="other", created="2026-09-01T00:00:00Z"),
    Document(id="x-d2", ticket="x", title="z", type="spec", created="2026-09-04T00:00:00Z"),
    Document(id="x-d3", ticket="x", title="a", type="plan", created="2026-09-02T00:00:00Z"),
    Document(id="x-d4", ticket="x", title="A", type="memo", created="2026-09-03T00:00:00Z"),
)
DOCUMENTED = replace(
    PROJECT,
    doc_types=("spec", "plan", "other"),
    required_docs=(("in_progress", ("spec", "plan")), ("closed", ("plan",))),
)


def test_documents_are_ordered_by_declared_type_then_title_with_undeclared_types_last():
    ordered = DOCUMENTED.ordered(SHUFFLED)

    assert [one.type for one in ordered] == ["spec", "plan", "other", "memo"]


def test_documents_of_one_type_are_ordered_by_title_ignoring_case():
    plans = (
        Document(id="y-d1", ticket="y", title="B", type="plan"),
        Document(id="y-d2", ticket="y", title="a", type="plan"),
    )

    # By code point "B" sorts before "a"; ignoring case, "a" comes first.
    assert [one.title for one in DOCUMENTED.ordered(plans)] == ["a", "B"]


def test_bare_type_names_are_ordered_the_same_way():
    assert DOCUMENTED.ordered_types(("plan", "memo", "spec")) == ("spec", "plan", "memo")


def test_the_types_a_ticket_owns_come_from_its_documents_or_else_its_listing_row():
    from_show = ticket("x", documents=SHUFFLED[1:3])
    from_row = ticket("y", doc_types=("plan", "spec"))

    assert DOCUMENTED.types_of(from_show) == ("spec", "plan")
    assert DOCUMENTED.types_of(from_row) == ("spec", "plan")
    assert not DOCUMENTED.types_of(ticket("z"))
    untyped = ticket("w", documents=(Document(id="w-d1", ticket="w", title="Loose", type=""),))
    assert not DOCUMENTED.types_of(untyped)


def test_every_status_whose_requirement_a_ticket_does_not_meet_is_named_with_what_it_lacks():
    nothing = ticket("a", status="closed")
    a_spec = ticket("b", status="in_progress", doc_types=("spec",))
    both = ticket("c", doc_types=("spec", "plan"))

    assert DOCUMENTED.missing_documents(nothing) == (
        ("in_progress", ("spec", "plan")),
        ("closed", ("plan",)),
    )
    assert DOCUMENTED.missing_documents(a_spec) == (
        ("in_progress", ("plan",)),
        ("closed", ("plan",)),
    )
    assert not DOCUMENTED.missing_documents(both)


def test_a_project_that_requires_nothing_finds_nothing_missing():
    assert not PROJECT.missing_documents(ticket("a"))


def test_missing_types_are_grouped_by_type_in_declared_order_with_every_status_needing_them():
    nothing = ticket("a", status="open")
    a_spec = ticket("b", status="in_progress", doc_types=("spec",))
    both = ticket("c", doc_types=("spec", "plan"))

    assert DOCUMENTED.missing_by_type(nothing) == (
        ("spec", ("in_progress",)),
        ("plan", ("in_progress", "closed")),
    )
    assert DOCUMENTED.missing_by_type(a_spec) == (("plan", ("in_progress", "closed")),)
    assert not DOCUMENTED.missing_by_type(both)


def test_a_ticket_is_live_unless_its_status_is_terminal():
    assert DOCUMENTED.is_live(ticket("a", status="open"))
    assert not DOCUMENTED.is_live(ticket("b", status="closed"))
