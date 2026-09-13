"""What is filed under what, with each parent's progress counted."""

from knotview.panel.tree import Tree
from tests.panel.declared import CHILD, ORPHAN, PARENT, DeclaredBacklog, ticket


def test_a_branch_shows_its_children_counted_and_the_parents_own_criteria(client):
    page = client(DeclaredBacklog()).get("/tree").text

    assert "children 0/1" in page
    assert "criteria 1/2" in page
    assert "filed under nothing" in page and "The orphan" in page


def test_a_complete_branch_that_is_still_open_says_so(client):
    done = ticket("pro-01m2bbbbbbbb", status="closed", parent="pro-01m2aaaaaaaa")
    page = client(DeclaredBacklog(live_value=(PARENT, done))).get("/tree").text

    assert "Every child is done and this is still open" in page
    assert "children 1/1" in page


def test_a_child_whose_parent_is_not_live_is_a_stray_and_every_live_ticket_appears_once():
    stray = ticket("pro-01m2eeeeeeee", parent="pro-01m2gone")

    shape = Tree.over((CHILD, ORPHAN, stray), terminal=("closed",))

    assert not shape.branches
    assert [one.id for one in shape.orphans] == ["pro-01m2dddddddd"]
    assert [one.id for one in shape.strays] == ["pro-01m2bbbbbbbb", "pro-01m2eeeeeeee"]


def test_strays_are_listed_on_the_tree_page(client):
    stray = ticket("pro-01m2eeeeeeee", title="The stray", parent="pro-01m2gone")
    page = client(DeclaredBacklog(live_value=(PARENT, CHILD, ORPHAN, stray))).get("/tree").text

    assert "filed under a parent that is not live" in page
    assert "The stray" in page


def test_branches_and_children_are_ordered_by_priority_then_id():
    low = ticket("pro-01m2ffffffff", priority=4, title="Low parent")
    kid = ticket("pro-01m2gggggggg", priority=0, parent="pro-01m2ffffffff")
    kid2 = ticket("pro-01m2hhhhhhhh", priority=0, parent="pro-01m2aaaaaaaa")

    shape = Tree.over((low, kid, PARENT, CHILD, kid2), terminal=("closed",))

    assert [b.parent.id for b in shape.branches] == ["pro-01m2aaaaaaaa", "pro-01m2ffffffff"]
    assert [c.id for c in shape.branches[0].children] == ["pro-01m2hhhhhhhh", "pro-01m2bbbbbbbb"]
    assert shape.branches[0].complete is False and shape.branches[0].total == 2
