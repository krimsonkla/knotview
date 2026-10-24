"""Related tickets drawn in full on the ticket page, each with the one fact its tab adds."""

import re
from dataclasses import dataclass, field

from knotview.panel.related import Related
from knotview.values.dependency import Dependency
from knotview.values.reference import Reference
from tests.panel.declared import PROJECT, DeclaredBacklog, ticket


def ref(one, *, status: str | None = None) -> Reference:
    """A reference to that ticket as `show` states one, its status as given or the ticket's own."""
    return Reference(id=one.id, title=one.title, status=status or one.status)


# An epic of four children and one id no ticket has. The first child is a parent itself.
GRAND_SHUT = ticket(
    "pro-01m2g1", status="closed", parent="pro-01m2c1", closed="2026-09-03T10:00:00Z"
)
GRAND_OPEN = ticket("pro-01m2g2", parent="pro-01m2c1")
BLOCKER = ticket("pro-01m2b1", title="The blocker")
C1 = ticket("pro-01m2c1", title="Child one", priority=1, parent="pro-01m2epic", tags=("auth",))
C2 = ticket("pro-01m2c2", title="Child two", priority=0, parent="pro-01m2epic", deps=(BLOCKER.id,))
C3 = ticket(
    "pro-01m2c3", title="Child three", status="in_progress", parent="pro-01m2epic", assignee="ann"
)
C4 = ticket(
    "pro-01m2c4",
    title="Child four",
    status="closed",
    priority=0,
    parent="pro-01m2epic",
    closed="2026-09-05T10:00:00Z",
)
GONE = Reference(id="pro-01m2gone", title="", status="", missing=True)
EPIC = ticket(
    "pro-01m2epic",
    title="The epic",
    type="epic",
    children=(ref(C4), ref(C1), GONE, ref(C3), ref(C2)),
)


@dataclass(kw_only=True)
class Treed(DeclaredBacklog):
    """A declared backlog with a dependency tree of the test's choosing for each ticket."""

    trees: dict[str, Dependency] = field(default_factory=dict)

    def dependencies(self, identifier: str) -> Dependency:
        """The declared tree, or a leaf."""
        return self.trees.get(identifier) or Dependency(id=identifier, title="", status="open")


def family(**held) -> Treed:
    """The epic's backlog: who is ready is knot's answer, declared rather than worked out."""
    given: dict = {
        "live_value": (EPIC, C1, C2, C3, GRAND_OPEN, BLOCKER),
        "closed_value": (C4, GRAND_SHUT),
        "ready_value": (C1, C3, GRAND_OPEN, BLOCKER),
        "blocked_value": (C2,),
    }
    return Treed(**{**given, **held})


def panel_of(text: str, name: str) -> str:
    """One tab panel alone, whitespace folded."""
    at = text.index(f'id="tab-{name}"')
    return re.sub(r"\s+", " ", text[at : text.index("</section>", at)])


def ids(text: str) -> list[str]:
    """The ids rows name, in order: a full row's mono id and a brief row's muted one."""
    return re.findall(r'<span class="kv-mono(?: kv-muted)?">(pro-01m2\w+)</span>', text)


def row(text: str, identifier: str) -> str:
    """The one row naming that id."""
    rows = re.split(r'(?=<div class="kv-row")', text)
    return next(one for one in rows if f">{identifier}<" in one)


def test_children_are_full_rows_open_first_by_priority_then_status_with_closed_and_missing_last(
    client,
):
    children = panel_of(client(family()).get(f"/ticket/{EPIC.id}").text, "children")

    assert ids(children) == [C2.id, C1.id, C3.id, C4.id, GONE.id]
    assert 'href="/tickets?tag=auth"' in row(children, C1.id)
    assert 'href="/tickets?assignee=ann"' in row(children, C3.id)
    assert 'class="kv-badge p0"' in row(children, C2.id)
    assert "no ticket has this id" in row(children, GONE.id)


def test_the_children_tab_counts_each_status_and_how_many_are_ready(client):
    children = panel_of(client(family()).get(f"/ticket/{EPIC.id}").text, "children")

    assert (
        '<p class="kv-muted kv-tally">2 open · 1 in_progress · 1 closed · 2 ready</p>' in children
    )


def test_a_child_that_is_a_parent_says_how_many_of_its_children_are_closed(client):
    children = panel_of(client(family()).get(f"/ticket/{EPIC.id}").text, "children")

    assert "1 of 2 children closed" in row(children, C1.id)
    assert "children closed" not in row(children, C2.id)


def test_siblings_are_full_rows_with_their_own_tally(client):
    text = client(family()).get(f"/ticket/{C1.id}").text
    at = text.index("also under")
    siblings = re.sub(r"\s+", " ", text[at : text.index("</section>", at)])

    assert ids(siblings) == [C2.id, C3.id, C4.id, GONE.id]
    assert "1 open · 1 in_progress · 1 closed · 1 ready</p>" in siblings


def test_a_tally_without_a_ready_ticket_does_not_count_none(client):
    shut = ticket("pro-01m2epic", type="epic", children=(ref(C4),))

    text = client(family(live_value=(shut, C1))).get(f"/ticket/{shut.id}").text

    assert '<p class="kv-muted kv-tally">1 closed</p>' in text


# A ticket blocked by three, and blocking two.
WAITS = ticket("pro-01m2w0", title="Waits", deps=("pro-01m2x1", "pro-01m2x2", "pro-01m2x3"))
X1 = ticket("pro-01m2x1", title="Ready one", priority=2)
X2 = ticket("pro-01m2x2", title="Stuck one", priority=0, deps=("pro-01m2y1", "pro-01m2y2"))
X3 = ticket("pro-01m2x3", title="Done one", status="closed", closed="2026-09-01T10:00:00Z")
Y1 = ticket("pro-01m2y1")
Y2 = ticket("pro-01m2y2")
LAST = ticket("pro-01m2v1", title="Only on me", priority=3, deps=(WAITS.id,))
SHARED = ticket("pro-01m2v2", title="Also on another", priority=0, deps=(WAITS.id, Y1.id))
WAITS_READ = ticket(
    WAITS.id,
    title="Waits",
    deps=WAITS.deps,
    blockers=(ref(X3), ref(X1), ref(X2)),
    blocking=(ref(SHARED), ref(LAST)),
)


def waiting(**held) -> Treed:
    """The waiting ticket's backlog, read in full where `show` would, listed elsewhere."""
    given: dict = {
        "live_value": (WAITS_READ, X1, X2, Y1, Y2, LAST, SHARED),
        "closed_value": (X3,),
        "ready_value": (X1, Y1, Y2),
    }
    return Treed(**{**given, **held})


def test_open_blockers_say_whether_they_can_start_and_closed_ones_sink_saying_when(client):
    relations = panel_of(client(waiting()).get(f"/ticket/{WAITS.id}").text, "relations")
    blocked_by = relations[: relations.index(">blocking <")]

    assert ids(blocked_by) == [X2.id, X1.id, X3.id]
    assert '<span class="kv-dot q-ready">ready to start</span>' in row(blocked_by, X1.id)
    assert '<span class="kv-dot q-blocked">blocked by 2</span>' in row(blocked_by, X2.id)
    assert re.search(
        r"<span>closed <time class=\"ago\"[^>]*>[^<]*ago</time></span>", row(blocked_by, X3.id)
    )


def test_the_ticket_it_is_the_only_blocker_of_comes_first_marked(client):
    relations = panel_of(client(waiting()).get(f"/ticket/{WAITS.id}").text, "relations")
    blocking = relations[relations.index(">blocking <") :]

    assert ids(blocking) == [LAST.id, SHARED.id]
    assert ">only blocker</span>" in row(blocking, LAST.id)
    assert "only blocker" not in row(blocking, SHARED.id)


def test_linked_tickets_are_full_rows_and_one_no_listing_holds_is_drawn_from_its_reference(
    client,
):
    stray = Reference(id="pro-01m2stray", title="Gone since", status="open")
    me = ticket("pro-01m2me", linked=(ref(X1), stray))

    linked = panel_of(client(waiting(live_value=(me, X1))).get(f"/ticket/{me.id}").text, "linked")

    assert 'href="/tickets?type=task"' in row(linked, X1.id)
    assert '<a class="title" href="/ticket/pro-01m2stray">Gone since</a>' in linked
    assert '<span class="kv-mono kv-muted">pro-01m2stray</span>' in linked


def test_related_rows_are_not_marked_since_the_last_look(client):
    text = client(family()).get(f"/ticket/{EPIC.id}").text

    assert "data-updated" not in panel_of(text, "children")


def test_the_reader_s_tags_do_not_narrow_what_a_ticket_is_related_to(client):
    browser = client(family())

    text = browser.get(
        f"/ticket/{EPIC.id}", headers={"cookie": "knotview_tags=nothing-has-this"}
    ).text

    assert ids(panel_of(text, "children")) == [C2.id, C1.id, C3.id, C4.id, GONE.id]


def test_each_node_of_the_tree_carries_its_priority_its_assignee_and_whether_it_can_start(client):
    owned = ticket("pro-01m2x1", title="Ready one", assignee="bo")
    tree = Dependency(
        id=WAITS.id,
        title="Waits",
        status="open",
        deps=(
            Dependency(id=X2.id, title=X2.title, status="open"),
            Dependency(id=owned.id, title=owned.title, status="open"),
            Dependency(id=X3.id, title=X3.title, status="closed"),
            Dependency(id="pro-01m2stray", title="Unlisted", status="open"),
        ),
    )
    backlog = waiting(trees={WAITS.id: tree})
    backlog.live_value = (*backlog.live_value[:1], owned, *backlog.live_value[2:])

    graph = panel_of(client(backlog).get(f"/ticket/{WAITS.id}").text, "graph")
    nodes = graph.split("<li>")[1:]

    assert '<span class="kv-badge p0">P0</span>' in nodes[0]
    assert 'class="kv-dot q-blocked" title="waits on 2 tickets not yet closed">blocked<' in nodes[0]
    assert '<span class="kv-muted">bo</span>' in nodes[1] and ">ready</span>" in nodes[1]
    assert '<span class="kv-badge p2">P2</span>' in nodes[2] and "q-" not in nodes[2]
    assert "kv-badge" not in nodes[3] and "Unlisted" in nodes[3]


def test_an_id_no_listing_holds_still_counts_as_in_the_way():
    related = Related.over(PROJECT, live=(X2, Y1), closed=(), ready=())

    assert related.waiting_on(X2) == (Y1.id, "pro-01m2y2")
    assert related.relative(ref(X2)).waiting_on == (Y1.id, "pro-01m2y2")


def test_the_tally_counts_no_missing_reference_and_an_undeclared_status_comes_after_closed():
    parked = ticket("pro-01m2p", status="parked")
    related = Related.over(PROJECT, live=(parked, C1), closed=(C4,), ready=())

    relatives = related.by_status(related.relatives((GONE, ref(parked), ref(C4), ref(C1))))

    assert [one.reference.id for one in relatives] == [C1.id, C4.id, parked.id, GONE.id]
    assert related.tally(relatives) == (("open", 1), ("closed", 1), ("parked", 1))


def test_without_the_ticket_the_page_is_about_nothing_is_an_only_blocker():
    related = Related.over(PROJECT, live=(LAST,), closed=(), ready=())

    assert not related.relative(ref(LAST)).only_blocker
    assert related.relative(ref(LAST), of=WAITS.id).only_blocker
