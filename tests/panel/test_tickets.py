"""Every ticket the filters admit, in the order asked for, with every filter kept in the links."""

import pytest

from knotview.panel.selection import ANY, Selection
from tests.panel.declared import CHILD, ORPHAN, PARENT, PROJECT, DeclaredBacklog, ticket

NAMES = ("The parent", "The child", "The orphan", "The closed one")


def titles(page: str) -> list[str]:
    """Which of the declared tickets the page shows, in the page's order of first mention."""
    return [name for name in NAMES if name in page]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", ["The parent", "The child", "The orphan"]),
        ("type=bug", ["The orphan"]),
        ("status=in_progress", ["The child"]),
        ("priority=1", ["The parent"]),
        ("mode=afk", ["The child"]),
        ("assignee=someone", ["The orphan"]),
        ("assignee=nobody", ["The parent", "The child"]),
        ("component=7", []),
        ("tag=auth", ["The parent"]),
        ("q=orphan", ["The orphan"]),
        ("q=pro-01m2bbbb", ["The child"]),
        ("q=p0", ["The parent"]),
        ("type=nonsense", ["The parent", "The child", "The orphan"]),
        ("closed=1", ["The parent", "The child", "The orphan", "The closed one"]),
        ("closed=1&status=closed", ["The closed one"]),
    ],
)
def test_each_filter_narrows_and_an_undeclared_value_is_dropped(client, query, expected):
    page = client(DeclaredBacklog()).get(f"/tickets?{query}").text

    assert titles(page) == expected


def test_the_summary_counts_shown_of_held_and_the_clear_link_appears_only_when_filtering(client):
    plain = client(DeclaredBacklog()).get("/tickets").text
    narrowed = client(DeclaredBacklog()).get("/tickets?type=bug").text

    assert "3 of 3" in plain and 'class="clear"' not in plain
    assert "1 of 3" in narrowed and '<a class="clear" href="/tickets">clear</a>' in narrowed
    assert "type bug" in narrowed


def test_orders_priority_first_by_default_and_newest_first_by_update(client):
    by_priority = client(DeclaredBacklog()).get("/tickets").text
    by_update = client(DeclaredBacklog()).get("/tickets?order=updated").text

    assert (
        by_priority.index("The parent")
        < by_priority.index("The child")
        < by_priority.index("The orphan")
    )
    assert by_update.index("The child") < by_update.index("The parent")


def test_ties_break_on_id_and_title_order_ignores_case(client):
    first = ticket("pro-01m2zzzzzzzz", title="alpha")
    second = ticket("pro-01m2yyyyyyyy", title="Beta")
    backlog = DeclaredBacklog(live_value=(first, second))

    by_priority = client(backlog).get("/tickets").text
    by_title = client(backlog).get("/tickets?order=title").text
    by_created = client(backlog).get("/tickets?order=created").text
    by_id = client(backlog).get("/tickets?order=id").text

    assert by_priority.index("Beta") < by_priority.index("alpha")
    assert by_title.index("alpha") < by_title.index("Beta")
    # A descending order reverses the id tie-break with it, so the higher id leads on a tie.
    assert by_created.index("alpha") < by_created.index("Beta")
    assert by_id.index("Beta") < by_id.index("alpha")


def test_a_selection_round_trips_through_its_query_string_and_omits_the_defaults():
    asked = Selection.asked(
        PROJECT, {"type": "bug", "order": "priority", "closed": "yes", "q": " x "}
    )

    assert asked.query_string() == "type=bug&q=x&closed=1"
    assert asked.query_string(order="title") == "type=bug&q=x&order=title&closed=1"
    assert not Selection().query_string()
    assert Selection.asked(PROJECT, {"assignee": " "}).assignee == ANY


def test_the_applied_filters_are_named_for_the_summary():
    assert Selection(type="bug", query="x").applied() == (("type", "bug"), ("matching", "x"))
    assert Selection().filtering is False


def test_matching_and_ordering_as_values():
    narrowed = Selection(tag="auth")
    assert narrowed.matches(PARENT) and not narrowed.matches(CHILD)
    assert Selection(query="nothing").matches(ORPHAN) is False
    assert Selection(order="id").ordered((ORPHAN, PARENT))[0] is PARENT


def test_leverage_orders_highest_first_and_level_lowest_first_with_unknowns_last(client):
    high = ticket("pro-01m2zzzzzzzz", title="High leverage", leverage=3, level=2)
    low = ticket("pro-01m2yyyyyyyy", title="Low leverage", leverage=1, level=0)
    unknown = ticket("pro-01m2xxxxxxxx", title="No metrics")
    backlog = DeclaredBacklog(live_value=(unknown, low, high))

    by_leverage = client(backlog).get("/tickets?order=leverage").text
    by_level = client(backlog).get("/tickets?order=level").text

    assert by_leverage.index("High leverage") < by_leverage.index("Low leverage")
    assert by_leverage.index("Low leverage") < by_leverage.index("No metrics")
    assert by_level.index("Low leverage") < by_level.index("High leverage")
    assert by_level.index("High leverage") < by_level.index("No metrics")


def test_the_metric_columns_show_the_number_or_a_dash(client):
    backlog = DeclaredBacklog(live_value=(ticket("pro-01m2zzzzzzzz", leverage=3, level=2), PARENT))
    page = client(backlog).get("/tickets").text

    assert 'href="/tickets?order=leverage">lev</a>' in page
    assert 'href="/tickets?order=level">lvl</a>' in page
    assert "—" in page and ">3<" in page.replace("\n", "").replace(" ", "")


def test_a_component_filter_keeps_one_island_and_shows_in_the_summary(client):
    same = ticket("pro-01m2zzzzzzzz", title="Same island", component=3)
    other = ticket("pro-01m2yyyyyyyy", title="Other island", component=4)
    page = client(DeclaredBacklog(live_value=(same, other))).get("/tickets?component=3").text

    assert "Same island" in page and "Other island" not in page
    assert "component 3" in page


def test_rows_carry_their_updated_instant_and_the_bar_has_a_since_marker(client):
    page = client(DeclaredBacklog()).get("/tickets").text

    assert 'data-updated="2026-09-04T10:00:00.000000Z"' in page
    assert 'id="since"' in page and 'src="/static/follow.js"' in page


def test_an_assignee_column_with_one_value_is_dropped_and_said_once(client):
    same = (ticket("pro-01m2zzzzzzzz"), ticket("pro-01m2yyyyyyyy"))
    page = client(DeclaredBacklog(live_value=same)).get("/tickets").text

    assert "all unassigned" in page and "<th>assignee</th>" not in page and "nobody" not in page


def test_the_assignee_column_stays_when_values_differ_or_the_filter_is_on(client):
    mixed = client(DeclaredBacklog()).get("/tickets").text
    filtered = client(DeclaredBacklog(live_value=(ORPHAN,))).get("/tickets?assignee=someone").text

    assert "<th>assignee</th>" in mixed and "nobody" in mixed
    assert "<th>assignee</th>" in filtered and "all assigned to" not in filtered


def test_the_instant_column_shows_whichever_order_is_on(client):
    by_updated = client(DeclaredBacklog(live_value=(CHILD,))).get("/tickets").text
    by_created = client(DeclaredBacklog(live_value=(CHILD,))).get("/tickets?order=created").text

    assert '<td class="muted" title="updated">2026-09-04 10:00</td>' in by_updated
    assert '<td class="muted" title="created">2026-09-01 10:00</td>' in by_created


def test_each_applied_filter_is_a_chip_whose_link_drops_only_it(client):
    page = client(DeclaredBacklog()).get("/tickets?type=task&q=child").text

    assert 'href="/tickets?q=child"' in page and 'href="/tickets?type=task"' in page
    assert Selection(type="task", query="child").without("matching") == "type=task"
    assert not Selection(type="task").without("type")
