"""What is filed under what, to any depth, with every live ticket on the page exactly once."""

from knotview.panel.tree import Tree
from tests.panel.declared import CHILD, ORPHAN, PARENT, DeclaredBacklog, ticket

GRANDCHILD = ticket("pro-01m2gggggggg", title="The grandchild", parent="pro-01m2bbbbbbbb")
STRAY = ticket("pro-01m2eeeeeeee", title="The stray", parent="pro-01m2gone")


def test_children_nest_under_their_parent_to_any_depth():
    shape = Tree.over((PARENT, CHILD, GRANDCHILD, ORPHAN))

    (root,) = shape.roots
    assert root.ticket is PARENT
    (child,) = root.children
    assert child.ticket is CHILD and child.children[0].ticket is GRANDCHILD
    assert (root.total, root.beneath, child.total, child.beneath) == (1, 2, 1, 1)
    assert (root.met, root.criteria) == (1, 2)


def test_every_live_ticket_appears_exactly_once():
    live = (PARENT, CHILD, GRANDCHILD, ORPHAN, STRAY)

    shape = Tree.over(live)

    assert sorted(t.id for t in shape.everything()) == sorted(t.id for t in live)
    assert [t.id for t in shape.orphans] == [ORPHAN.id]
    assert [t.id for t in shape.strays] == [STRAY.id]


def test_a_stray_with_children_is_a_root_of_its_own():
    kid = ticket("pro-01m2kkkkkkkk", parent=STRAY.id)

    shape = Tree.over((STRAY, kid))

    assert [r.ticket.id for r in shape.roots] == [STRAY.id]
    assert not shape.strays


def test_roots_and_children_are_ordered_by_priority_then_id():
    low = ticket("pro-01m2ffffffff", priority=4, title="Low parent")
    kid = ticket("pro-01m2gggggggg", priority=0, parent="pro-01m2ffffffff")
    kid2 = ticket("pro-01m2hhhhhhhh", priority=0, parent="pro-01m2aaaaaaaa")

    shape = Tree.over((low, kid, PARENT, CHILD, kid2))

    assert [r.ticket.id for r in shape.roots] == ["pro-01m2aaaaaaaa", "pro-01m2ffffffff"]
    assert [c.ticket.id for c in shape.roots[0].children] == [
        "pro-01m2hhhhhhhh",
        "pro-01m2bbbbbbbb",
    ]


def test_the_page_nests_a_grandchild_inside_its_parent_and_lists_the_rest(client):
    live = (PARENT, CHILD, GRANDCHILD, ORPHAN, STRAY)
    page = client(DeclaredBacklog(live_value=live)).get("/tree").text

    opened = page.index('data-fold="pro-01m2aaaaaaaa"')
    inner = page.index('data-fold="pro-01m2bbbbbbbb"')
    leaf = page.index("The grandchild")
    assert opened < inner < leaf < page.index("</details>", leaf)
    assert "children 1" in page and "beneath 2" in page and "criteria 1/2" in page
    assert "filed under a parent that is not live" in page and "The stray" in page
    assert "filed under nothing" in page and "The orphan" in page
    assert 'src="/static/tree.js?v=' in page
    assert page.count("The grandchild") == 1


def test_a_root_shows_its_island_as_a_link_to_that_component(client):
    islanded = ticket("pro-01m2iiiiiiii", title="Islanded", component=2)
    kid = ticket("pro-01m2jjjjjjjj", parent="pro-01m2iiiiiiii", component=2)
    page = client(DeclaredBacklog(live_value=(islanded, kid))).get("/tree").text

    assert 'href="/tickets?component=2"' in page and "island 2" in page
