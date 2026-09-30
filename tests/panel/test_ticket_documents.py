"""A ticket's documents on its page, and a missing required document among what blocks it."""

from dataclasses import replace

from tests.panel.declared import CHILD, CLOSED, ORPHAN, PARENT, PARENT_DOCUMENTS, PROJECT
from tests.panel.declared import DeclaredBacklog, ticket

PLAN, SPEC = PARENT_DOCUMENTS
# spec and plan to enter in_progress, spec again to enter review.
GATED = replace(
    PROJECT,
    statuses=(*PROJECT.statuses, "review"),
    required_docs=(("in_progress", ("spec", "plan")), ("review", ("spec",))),
)


def page(client, identifier: str, **backlog) -> str:
    """One ticket page over a declared backlog."""
    return client(DeclaredBacklog(**backlog)).get(f"/ticket/{identifier}").text


def card(text: str) -> str:
    """The documents card alone."""
    at = text.index('id="documents"')
    return text[at : text.index("</section>", at)]


def test_documents_come_first_in_declared_type_order_with_their_last_change(client):
    text = page(client, PARENT.id)

    documents = card(text)
    assert text.index('id="documents"') < text.index("acceptance <span")
    assert documents.index("Design spec") < documents.index("Rollout plan")
    for one in (SPEC, PLAN):
        assert f'href="/document/{one.id}">{one.title}</a>' in documents
        assert f'<span class="id">{one.id}</span>' in documents
    assert '<span class="doctype">spec</span>' in documents
    assert documents.count("updated <time") == 2
    assert '<a class="chip" href="#documents">2 documents</a>' in text


def test_a_refused_document_list_falls_back_to_the_documents_show_stated(client):
    text = page(client, PARENT.id, documents_refused=True)

    documents = card(text)
    assert "Design spec" in documents and "Rollout plan" in documents
    assert "updated <time" not in documents


def test_a_ticket_with_no_documents_shows_no_card_and_no_chip(client):
    text = page(client, ORPHAN.id)

    assert 'id="documents"' not in text and "documents</a>" not in text


def blocked(text: str) -> str:
    """The blocked-by card alone."""
    graph = text[text.index('<section class="graph">') :]
    at = graph.index("blocked by")
    return graph[at : graph.index("</div>", at)]


def test_missing_types_are_quiet_rows_among_the_blockers_and_are_counted(client):
    text = page(client, CHILD.id, project_value=GATED)

    rows = blocked(text)
    assert 'title="the tickets blocking this, and the required documents it lacks"' in rows
    assert ">4</span" in rows
    assert '<span class="doctype missing">spec</span>' in rows
    assert "no spec attached" in rows and "no plan attached" in rows
    assert rows.index("no spec attached") < rows.index("no plan attached")


def test_a_type_two_statuses_need_is_one_row_naming_both(client):
    rows = blocked(page(client, CHILD.id, project_value=GATED))

    assert rows.count("no spec attached") == 1
    assert "needed to enter in_progress, review" in rows


def test_a_closed_ticket_lacks_nothing(client):
    shut = replace(CLOSED, blockers=CHILD.blockers)

    text = page(client, shut.id, project_value=GATED, closed_value=(shut,))

    assert "no spec attached" not in text


def test_a_ticket_with_no_blockers_and_nothing_missing_has_no_blocked_by_card(client):
    text = page(client, ORPHAN.id)

    graph = text[text.index('<section class="graph">') :]
    assert "blocked by" not in graph and "required documents it lacks" not in graph


def test_a_missing_document_row_never_says_missing(client):
    lacking = ticket("pro-01m2eeeeeeee", status="in_progress", title="Lacking")

    rows = blocked(page(client, lacking.id, project_value=GATED, live_value=(lacking,)))

    assert "no spec attached" in rows and 'chip muted">missing' not in rows


def test_one_document_is_counted_in_the_singular(client):
    text = page(client, PARENT.id, documents_value={PARENT.id: (SPEC,)})

    assert '<a class="chip" href="#documents">1 document</a>' in text
