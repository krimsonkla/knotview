"""Documents on the overview, the tree and the footer."""

from dataclasses import replace
from urllib.parse import parse_qs

import pytest

from knotview.panel.selection import Selection
from knotview.panel.tags import COOKIE
from tests.panel.declared import CHILD, ORPHAN, PARENT, PROJECT, DeclaredBacklog
from tests.panel.test_list_documents import REQUIRING


def page(client, path: str, **backlog) -> str:
    """One rendered page over a declared backlog whose project requires a spec and a plan."""
    return client(DeclaredBacklog(project_value=REQUIRING, **backlog)).get(path).text


def test_a_link_to_one_type_replaces_the_chosen_types_and_keeps_every_other_filter():
    chosen = Selection(type="task", docs=("plan",), undocumented=True)

    assert parse_qs(chosen.having("spec")) == {"type": ["task"], "doc": ["spec"]}


def test_a_change_naming_a_document_type_is_refused_rather_than_added_to_the_chosen_ones():
    with pytest.raises(TypeError, match="having"):
        Selection(docs=("plan",)).query_string(doc="spec")


def section(text: str, start: str, end: str) -> str:
    """The part of a page between two markers, so an assertion is about one row."""
    at = text.index(start)
    return text[at : text.index(end, at)]


def test_a_tree_node_shows_its_types_in_order_linking_to_its_documents(client):
    text = page(client, "/tree")

    row = section(text, "The parent", "</summary>")
    assert row.index(">spec<") < row.index(">plan<")
    assert 'href="/ticket/pro-01m2aaaaaaaa#documents"' in row


def test_a_live_leaf_shows_what_it_lacks_dashed(client):
    text = page(client, "/tree")

    leaf = section(text, "The child", "</div>")
    assert 'class="doctype missing" title="needed to enter in_progress">spec<' in leaf


def test_a_closed_leaf_draws_no_dashed_type(client):
    shut = replace(CHILD, status="closed")

    text = page(client, "/tree", live_value=(PARENT, shut))

    assert 'class="doctype missing"' not in section(text, "The child", "</div>")


def test_an_orphan_row_on_the_tree_shows_its_dashed_types(client):
    text = page(client, "/tree")

    row = section(text, "The orphan", "</tr>")
    assert 'class="doctype missing"' in row


def test_the_overview_counts_live_tickets_by_the_types_they_own_linking_to_each_list(client):
    second = replace(CHILD, documents=PARENT.documents[1:])

    text = page(client, "/", live_value=(PARENT, second, ORPHAN))

    card = section(text, "<h2>by document</h2>", "</div>")
    assert "tickets owning each type" in card
    for kind, count in (("spec", 2), ("plan", 1), ("other", 0)):
        link = f'<a href="/tickets?doc={kind}">{kind}</a>'
        assert link in card and card.index(link) < card.index(f'<span class="num">{count}</span>')


def test_no_documents_card_when_the_chosen_tag_leaves_no_ticket_owning_one(client):
    tagged = replace(ORPHAN, tags=("ops",))
    browser = client(DeclaredBacklog(project_value=REQUIRING, live_value=(PARENT, tagged)))
    browser.cookies.set(COOKIE, "ops")

    text = browser.get("/").text

    assert "The orphan" in text and "by document" not in text


def test_a_type_row_links_to_that_type_alone_whatever_was_chosen(client):
    text = page(client, "/?doc=plan&nodocs=1&type=task")

    # The overview ignores its URL (kno-01m3qneqctfh), so the row carries its type and nothing else.
    card = section(text, "<h2>by document</h2>", "</ul>")
    assert '<a href="/tickets?doc=spec">spec</a>' in card


def test_the_footer_counts_the_projects_documents_zero_included(client):
    counted = client(DeclaredBacklog(project_value=replace(PROJECT, doc_count=3))).get("/tree").text
    none = client(DeclaredBacklog(project_value=replace(PROJECT, doc_count=0))).get("/tree").text

    assert "3 documents" in counted and "0 documents" in none
