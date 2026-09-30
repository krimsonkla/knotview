"""The page that reads one document, its tabs, and the reads it degrades around."""

from dataclasses import replace

import pytest

from knotview.values.document import Document
from knotview.values.missing_document import MissingDocument
from tests.panel.declared import CLOSED, PARENT, PARENT_DOCUMENTS, DeclaredBacklog

PLAN, SPEC = PARENT_DOCUMENTS
BODY = "# Goal\n\nShip it, with `care`.\n\n## Steps\n\n- one\n- two\n"
WRITTEN = (replace(PLAN, body=BODY), SPEC)


def page(client, path: str, **backlog):
    """One response over a declared backlog holding the parent's plan and spec."""
    backlog.setdefault("documents_value", {PARENT.id: WRITTEN})
    return client(DeclaredBacklog(**backlog)).get(path)


def test_the_double_resolves_a_whole_id_then_a_start_only_one_id_begins_with():
    held = DeclaredBacklog()

    assert held.document(PLAN.id) == PLAN
    assert held.document("pro-01m2aaaaaaaa-d2").id == PLAN.id
    with pytest.raises(MissingDocument):
        held.document("pro-01m2aaaaaaaa-d")
    with pytest.raises(MissingDocument):
        held.document("pro-01m2aaaaaaaa-dx")
    with pytest.raises(MissingDocument):
        held.document("pro-01m2aaaa")


def test_a_document_reads_in_full_under_its_ticket(client):
    text = page(client, f"/document/{PLAN.id}").text

    assert '<a href="/ticket/pro-01m2aaaaaaaa">The parent</a>' in text
    assert text.count("<h1") == 1 and "<h1>Rollout plan</h1>" in text
    assert '<span class="doctype">plan</span>' in text and PLAN.id in text
    assert '<h2 id="doc-goal">Goal</h2>' in text and "<code>care</code>" in text
    assert 'href="#doc-goal"' in text and 'href="#doc-steps"' in text
    assert f'updated <time class="stamp" datetime="{PLAN.updated}"' in text


def test_an_unknown_document_is_a_404_offering_the_list(client):
    answer = page(client, "/document/pro-01m2aaaaaaaa-dnope")

    assert answer.status_code == 404 and "document called pro-01m2aaaaaaaa-dnope" in answer.text


def test_an_empty_document_says_so(client):
    empty = (replace(PLAN, body=""),)

    text = page(client, f"/document/{PLAN.id}", documents_value={PARENT.id: empty}).text

    assert "This document is empty." in text


def test_a_document_whose_ticket_knot_cannot_find_still_reads(client):
    stray = Document(
        id="pro-01m2zzzzzzzz-d1x",
        ticket="pro-01m2zzzzzzzz",
        title="Stray",
        type="other",
        body="Still here.\n",
    )

    answer = page(client, f"/document/{stray.id}", documents_value={"pro-01m2zzzzzzzz": (stray,)})

    assert answer.status_code == 200 and "Still here." in answer.text
    assert "pro-01m2zzzzzzzz" in answer.text and "ticket called" not in answer.text


def test_a_closed_tickets_document_reads_the_same(client):
    note = Document(
        id=f"{CLOSED.id}-d9note", ticket=CLOSED.id, title="Note", type="other", body="Done.\n"
    )

    spec = Document(id=f"{CLOSED.id}-d1spec", ticket=CLOSED.id, title="Spec", type="spec")

    answer = page(client, f"/document/{note.id}", documents_value={CLOSED.id: (note, spec)})

    assert answer.status_code == 200 and "Done." in answer.text
    assert f'href="/document/{note.id}" aria-current="page"' in answer.text
    assert "2 of 2" in answer.text


def test_tabs_follow_the_declared_type_order_and_mark_the_current_one(client):
    text = page(client, f"/document/{PLAN.id}").text

    tabs = text[text.index('class="tabs"') :]
    tabs = tabs[: tabs.index("</nav>")]
    assert tabs.index("Design spec") < tabs.index("Rollout plan")
    assert f'href="/document/{PLAN.id}" aria-current="page"' in tabs
    assert "2 of 2" in text


def test_the_all_menu_lists_every_document_under_its_type(client):
    text = page(client, f"/document/{PLAN.id}").text

    menu = text[text.index('<details class="all"') :]
    menu = menu[: menu.index("</details>")]
    assert menu.index(">spec<") < menu.index("Design spec") < menu.index(">plan<")
    assert menu.index(">plan<") < menu.index("Rollout plan")
    assert menu.count(f'datetime="{PLAN.updated}"') == 2


def test_a_start_of_an_id_still_marks_the_document_knot_resolved(client):
    text = page(client, "/document/pro-01m2aaaaaaaa-d2").text

    assert f'href="/document/{PLAN.id}" aria-current="page"' in text
    assert 'href="/document/pro-01m2aaaaaaaa-d2"' not in text


def test_a_lone_document_has_no_tabs_menu_or_position(client):
    text = page(client, f"/document/{PLAN.id}", documents_value={PARENT.id: WRITTEN[:1]}).text

    assert 'class="tabs"' not in text and 'class="all"' not in text and " of 1" not in text


def test_documents_of_one_type_share_one_heading_in_the_menu(client):
    second = replace(SPEC, id="pro-01m2aaaaaaaa-d8spec", title="Another spec")

    text = page(
        client, f"/document/{PLAN.id}", documents_value={PARENT.id: (*WRITTEN, second)}
    ).text

    menu = text[text.index('<details class="all"') :]
    menu = menu[: menu.index("</details>")]
    assert menu.count('class="group"') == 2
    assert menu.index("Another spec") < menu.index("Design spec") < menu.index(">plan<")


def test_an_id_that_is_not_safe_in_a_path_is_encoded_in_every_link(client):
    odd = replace(SPEC, id="pro-01m2aaaaaaaa-dx#y/z")

    text = page(client, f"/document/{PLAN.id}", documents_value={PARENT.id: (WRITTEN[0], odd)}).text

    assert 'href="/document/pro-01m2aaaaaaaa-dx%23y%2Fz"' in text
