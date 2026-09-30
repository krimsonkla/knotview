"""Integrity issues as values: their text, their path as a reader reads it, and what they link."""

from pathlib import Path

from knotview.reading.knot_command import _issue
from knotview.values.issue import Issue
from tests.reading.envelopes import envelope

ROOT = Path("/work/project")
MEMO = "/work/project/.tickets/docs/pro-1/pro-1-d5memo--memo.md"


def stated(code: str, ids=("pro-1-d5memo",), path: str = MEMO) -> dict:
    """One check issue as knot 0.15 states it."""
    held = {"severity": "error", "code": code, "message": "something is off"}
    if ids is not None:
        held["ids"] = list(ids)
    if path:
        held["path"] = path
    return held


def test_a_document_issue_inside_the_project_shows_its_path_from_the_root_and_links_it():
    issue = _issue(stated("invalid_doc_type"), ROOT)

    assert issue == Issue(
        text="invalid_doc_type: something is off",
        path=MEMO,
        shown=".tickets/docs/pro-1/pro-1-d5memo--memo.md",
        document_ids=("pro-1-d5memo",),
    )


def test_a_path_outside_the_project_is_shown_whole():
    elsewhere = "/elsewhere/docs/pro-1/pro-1-d1x--orphan.md"

    issue = _issue(stated("doc_unknown_ticket", ids=("pro-1-d1x",), path=elsewhere), ROOT)

    assert issue.shown == elsewhere and issue.document_ids == ("pro-1-d1x",)


def test_only_the_verified_document_codes_link():
    for code in ("legacy_documents_section", "duplicate_doc_id", "unknown_id", "a_new_code"):
        assert not _issue(stated(code), ROOT).document_ids
    for code in ("doc_directory_mismatch", "doc_id_owner_mismatch"):
        assert _issue(stated(code), ROOT).document_ids == ("pro-1-d5memo",)


def test_every_id_of_a_linkable_issue_links():
    issue = _issue(stated("doc_id_owner_mismatch", ids=("pro-1-da", "pro-1-db")), ROOT)

    assert issue.document_ids == ("pro-1-da", "pro-1-db")


def test_an_issue_with_no_ids_and_no_path_is_its_text_alone():
    issue = _issue(stated("unreachable_documents", ids=None, path=""), ROOT)

    assert issue == Issue(text="unreachable_documents: something is off")


def test_an_issue_knot_did_not_shape_as_a_mapping_is_its_text():
    assert _issue("a bare line", ROOT) == Issue(text="a bare line")


def test_the_project_root_is_taken_off_a_path_knot_wrote_into_its_message():
    issue = _issue(
        stated("unreachable_documents", ids=None, path="")
        | {"message": "documents sit at /work/project/.tickets/docs, not /elsewhere/d"},
        ROOT,
    )

    assert issue.text == "unreachable_documents: documents sit at .tickets/docs, not /elsewhere/d"


def test_the_recorded_document_issues_link_their_documents_and_the_ticket_one_does_not():
    """From knot 0.15's own answer. The paths come from the faults probe and the root from info's,
    which is the main probe: both are scrubbed to /probe, so each issue reads from the root it
    would have in one project; that is by construction, not a second probe mislabelled."""
    root = Path(envelope("info")["data"]["paths"]["project_root"])
    orphan, memo, legacy = (
        _issue(one, root) for one in envelope("check-documents")["data"]["issues"]
    )

    assert orphan.document_ids == ("pro-01m2zzzzzzzz-d1x",)
    assert orphan.shown == ".tickets/docs/pro-01m2zzzzzzzz/pro-01m2zzzzzzzz-d1x--orphan.md"
    assert memo.document_ids == ("pro-01m2aaaaaaaa-d5memo",)
    assert memo.text.startswith("invalid_doc_type: document")
    assert not legacy.document_ids and not legacy.path
    assert legacy.text.startswith("pro-01m2aaaaaaaa legacy_documents_section:")
