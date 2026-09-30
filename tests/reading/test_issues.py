"""Integrity issues as values: their text, their path as a reader reads it, and what they link."""

from pathlib import Path

import pytest

from knotview.reading.knot_command import LINKED, TICKET_CODES, _issue
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


# Restated here from the survey, not imported, so a code dropped from or added to the source
# fails a test rather than passing with it.
TICKET_CODE_NAMES = tuple("""
    invalid_status invalid_type invalid_mode invalid_priority terminal_outside_archive unknown_id
    acceptance_invalid legacy_acceptance_section reserved_section duplicate_section
    legacy_documents_section missing_required_field dep_cycle
    """.split())
NEITHER = (
    "duplicate_doc_id",
    "unreachable_documents",
    "invalid_active_status",
    "skill_stale",
    "frontmatter_parse_error",
)


@pytest.mark.parametrize("code", TICKET_CODE_NAMES)
def test_every_verified_ticket_code_links_its_ticket(code):
    issue = _issue(stated(code, ids=("pro-1",), path=""), ROOT)

    assert issue.ticket_ids == ("pro-1",) and not issue.document_ids
    assert issue.text == f"{code}: something is off"


def test_the_code_sets_are_disjoint_and_the_rest_are_in_neither():
    """Surveyed from knot 0.15.0's check.clj. duplicate_doc_id names an id knot refuses as
    ambiguous; the others always carry empty ids, and would link wrongly the day knot filled
    them, so they are pinned out of both sets."""
    assert set(TICKET_CODE_NAMES) == TICKET_CODES and not TICKET_CODES & LINKED
    assert not (TICKET_CODES | LINKED) & set(NEITHER)
    for code in NEITHER:
        issue = _issue(stated(code, ids=("x",)), ROOT)
        assert not issue.ticket_ids and not issue.document_ids


def test_a_cycle_links_each_ticket_once_since_its_message_already_closes_the_path():
    issue = _issue(stated("dep_cycle", ids=("a", "b", "c", "a"), path=""), ROOT)

    assert issue.ticket_ids == ("a", "b", "c")


def test_a_null_id_is_neither_linked_nor_written():
    """knot 0.15 emits ids [null] for invalid_priority on a ticket with no id."""
    issue = _issue(stated("invalid_priority", ids=(None,), path=""), ROOT)

    assert not issue.ticket_ids and "None" not in issue.text
    assert issue.text == "invalid_priority: something is off"
    plain = _issue(stated("a_new_code", ids=(None, "", "t-1"), path=""), ROOT)
    assert plain.text == "t-1 a_new_code: something is off"


def test_an_unknown_id_links_its_holder_and_leaves_the_missing_target_in_the_message():
    stated_issue = {
        "severity": "error",
        "code": "unknown_id",
        "ids": ["pro-1"],
        "field": "deps",
        "value": "pro-gone",
        "message": 'unknown id "pro-gone" referenced by "pro-1" via :deps',
    }

    issue = _issue(stated_issue, ROOT)

    assert issue.ticket_ids == ("pro-1",) and "pro-gone" in issue.text


def test_every_code_in_a_committed_check_recording_has_been_classified():
    """A code knot renames or adds reaches the panel first through a re-recording; this fails
    there rather than letting the new code be shown unlinked without anyone deciding so."""
    classified = TICKET_CODES | LINKED | set(NEITHER)
    recorded = {
        issue["code"]
        for name in ("check-issues", "check-clean")
        for issue in envelope(name)["data"]["issues"]
    }

    assert recorded and recorded <= classified
