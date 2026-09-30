"""The document shapes the recordings must carry, so later readers are written against real ones.

These read the recorded files only, so they run without knot; test_real_knot.py checks the same
recordings against the binary.
"""

from tests.reading.envelopes import envelope

LISTINGS = ("list", "ready", "blocked", "closed")


def test_the_parent_shows_both_its_documents_without_their_bodies():
    documents = envelope("show-parent")["data"]["documents"]

    assert {one["id"] for one in documents} == {
        "pro-01m2aaaaaaaa-d2plan",
        "pro-01m2aaaaaaaa-d7spec",
    }
    assert all(set(one) == {"id", "title", "type"} for one in documents)


def test_every_listing_has_a_row_owning_documents_and_list_and_ready_have_one_without():
    for name in LISTINGS:
        rows = envelope(name)["data"]
        assert any("doc_types" in row for row in rows), name
    for name in ("list", "ready"):
        assert any("doc_types" not in row for row in envelope(name)["data"]), name


def test_info_carries_the_document_configuration_and_count():
    data = envelope("info")["data"]

    assert data["project"]["knot_version"] == "0.15.0"
    assert data["paths"]["docs_path"] == "/probe/.tickets/docs"
    assert data["defaults"]["default_doc_type"] == "other"
    assert data["allowed_values"]["doc_types"] == ["spec", "plan", "other"]
    assert data["allowed_values"]["required_docs"] == {"in_progress": ["spec", "plan"]}
    assert data["counts"]["doc_count"] == 4


def test_both_checks_count_the_documents_they_scanned():
    assert envelope("check-issues")["data"]["scanned"]["docs"] == 4
    assert envelope("check-clean")["data"]["scanned"]["docs"] == 3
    assert not envelope("check-clean")["data"]["issues"]


def test_a_document_list_carries_the_times_and_a_document_show_carries_the_body():
    listed = envelope("document-list")["data"]
    shown = envelope("document-show")["data"]

    assert listed["ticket"] == "pro-01m2aaaaaaaa"
    assert all({"created", "updated"} <= set(one) for one in listed["documents"])
    assert len(listed["documents"]) == 2
    assert shown["id"] == "pro-01m2aaaaaaaa-d7spec"
    assert "| a | b |" in shown["body"]


def test_an_unknown_document_is_refused_with_its_own_code():
    refused = envelope("document-not-found")

    assert refused["ok"] is False
    assert refused["error"]["code"] == "doc_not_found"
