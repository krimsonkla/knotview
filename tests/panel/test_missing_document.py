"""A document that is not there is a page that is not there, not a backlog that cannot be read.

No page reads a document yet, so a route is added to one assembled app here to raise the refusal
through the real handlers. MissingDocument is a kind of the general refusal, which has its own
handler too, so only a real request shows the more specific one is chosen.
"""

from fastapi import Request
from fastapi.testclient import TestClient

from knotview.panel.app import panel
from tests.panel.declared import PARENT, PARENT_DOCUMENTS, DeclaredBacklog


def test_an_unknown_document_answers_404_offering_the_ticket_list():
    backlog = DeclaredBacklog()
    app = panel(backlog)

    async def reading(request: Request, document_id: str):  # pylint: disable=unused-argument
        backlog.document(document_id)

    app.add_api_route("/probe-document/{document_id}", reading, methods=["GET"])
    answer = TestClient(app, base_url="http://127.0.0.1").get("/probe-document/nope-d1")

    assert answer.status_code == 404
    assert "document called nope-d1" in answer.text
    assert 'href="/tickets"' in answer.text


def test_the_declared_backlog_reads_documents_as_knot_would():
    backlog = DeclaredBacklog()

    listed = backlog.documents(PARENT.id)

    assert [one.id for one in listed] == [one.id for one in PARENT.documents]
    assert all(one.updated and one.body is None for one in listed)
    assert backlog.document(PARENT_DOCUMENTS[1].id).body == "The spec.\n"
    assert not backlog.documents("pro-01m2dddddddd")
