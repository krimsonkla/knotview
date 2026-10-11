"""A ticket page leads with what matters and folds the rest."""

from knotview.values.document import Document
from knotview.values.reference import Reference
from tests.panel.declared import DeclaredBacklog, ticket

LONG = "first\n\nsecond\n\nthird hidden"


def _page(client, one, docs=()):
    backlog = DeclaredBacklog(live_value=(one,), documents_value={one.id: tuple(docs)})
    return client(backlog).get(f"/ticket/{one.id}").text


def test_documents_come_before_the_description_and_design_is_folded(client):
    spec = Document(id="kno-p1-d1", ticket="kno-p1", title="The spec", type="spec")
    one = ticket("kno-p1", sections={"description": "what", "design": "how"}, documents=(spec,))

    page = _page(client, one, docs=(spec,))

    assert page.index('id="documents"') < page.index("what")
    assert '<details class="kv-card kv-fold" data-fold="t-kno-p1-design"' in page
    assert 'data-fold="t-kno-p1-design" data-fold-store="session" open' not in page


def test_a_long_description_folds_after_two_blocks(client):
    page = _page(client, ticket("kno-p2", sections={"description": LONG}))

    assert page.index("second") < page.index("Read the full description")
    assert page.index("Read the full description") < page.index("third hidden")


def test_a_short_description_has_nothing_to_unfold(client):
    page = _page(client, ticket("kno-p5", sections={"description": "just this"}))

    assert "just this" in page and "Read the full description" not in page


def test_empty_sections_tabs_and_sidebar_entries_are_not_drawn(client):
    page = _page(client, ticket("kno-p3"))

    for absent in (
        'id="documents"',
        'id="tab-children"',
        'id="tab-relations"',
        ">External<",
        "data-tabs",
        ">Assignee<",
        ">Tags<",
    ):
        assert absent not in page, absent


def test_children_render_in_a_tab_panel_named_in_the_tab_bar(client):
    parent = ticket("kno-p4", children=(Reference(id="kno-c1", title="a child", status="open"),))

    page = _page(client, parent)

    assert '<nav class="kv-tabbar" data-tabs' in page
    assert 'href="#tab-children" data-tab="tab-children"' in page
    assert '<section class="kv-tabpanel" id="tab-children"' in page
    assert 'src="/static/fold.js?v=' in page


def test_an_unknown_ticket_is_a_404_in_the_new_shell(client):
    answer = client(DeclaredBacklog()).get("/ticket/kno-nope")

    assert answer.status_code == 404 and 'class="kv-header"' in answer.text
