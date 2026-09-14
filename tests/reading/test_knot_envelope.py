"""Reading knot's answer shape into this panel's values, from envelopes knot actually emitted."""

import pytest

from knotview.reading.knot_envelope import (
    answered,
    project_from,
    ticket_from,
    tickets_from,
    verdict,
)
from knotview.values.unreadable_backlog import UnreadableBacklog
from tests.reading.envelopes import envelope


def test_a_clean_check_is_data_with_no_issues():
    assert verdict(envelope("check-clean"), attempting="knot check")["issues"] == []


def test_a_check_with_issues_is_data_even_though_knot_says_not_ok():
    """knot's health verdict is ok:false co-emitted with data, which is the one documented
    carve-out from the envelope rule."""
    stated = envelope("check-issues")
    assert stated["ok"] is False

    issues = verdict(stated, attempting="knot check")["issues"]

    assert issues[0]["code"] == "unknown_id"


def test_a_refused_check_is_still_a_refusal():
    with pytest.raises(UnreadableBacklog, match="no ticket matching"):
        verdict(envelope("not-found"), attempting="knot check")


def test_not_ok_with_no_issues_key_is_a_failed_scan_not_a_clean_one():
    with pytest.raises(UnreadableBacklog, match="was refused"):
        verdict({"schema_version": 1, "ok": False, "data": {}}, attempting="knot check")


def test_not_ok_with_an_empty_issues_list_is_a_failed_scan_not_a_clean_one():
    with pytest.raises(UnreadableBacklog, match="was refused"):
        verdict({"schema_version": 1, "ok": False, "data": {"issues": []}}, attempting="knot check")


def test_the_verdict_still_checks_the_envelope_version():
    with pytest.raises(UnreadableBacklog, match="version 2"):
        verdict({"schema_version": 2, "ok": True, "data": {"issues": []}}, attempting="knot check")


def test_the_verdict_refuses_something_that_is_not_an_envelope():
    with pytest.raises(UnreadableBacklog, match="rather than an envelope"):
        verdict(["issues"], attempting="knot check")


def test_answered_returns_the_data():
    assert answered(envelope("check-clean"), attempting="x")["scanned"]["live"] == 1


def test_answered_refuses_a_not_ok_envelope_with_knots_own_message_and_code():
    with pytest.raises(UnreadableBacklog, match="no ticket matching nope") as refused:
        answered(envelope("not-found"), attempting="knot show")

    assert refused.value.code == "not_found"


def test_answered_refuses_a_not_ok_envelope_that_gives_no_reason():
    with pytest.raises(UnreadableBacklog, match="knot gave no reason"):
        answered({"schema_version": 1, "ok": False, "error": "text"}, attempting="knot show")


def test_answered_refuses_a_non_envelope_and_a_moved_version():
    with pytest.raises(UnreadableBacklog, match="rather than an envelope"):
        answered("nope", attempting="x")  # type: ignore[arg-type]
    with pytest.raises(UnreadableBacklog, match="version 0"):
        answered({"schema_version": 0}, attempting="x")


def test_the_project_is_read_from_info():
    project = project_from(envelope("info")["data"])

    assert (project.prefix, project.knot_version) == ("pro", "0.12.0")
    assert project.types == ("bug", "feature", "task", "epic", "chore")
    assert project.statuses == ("open", "in_progress", "closed")
    assert project.terminal_statuses == ("closed",)
    assert project.active_status == "in_progress"
    assert project.modes == ("afk", "hitl")
    assert project.priority_range == (0, 4)
    assert (project.live_count, project.archive_count) == (3, 1)
    assert project.tickets_path.endswith("/.tickets")


def test_a_project_with_no_name_is_called_unnamed():
    assert project_from(envelope("info")["data"]).name == "unnamed"


def test_a_project_stated_as_nothing_is_refused_and_a_half_stated_one_is_tolerated():
    with pytest.raises(UnreadableBacklog, match="no configuration"):
        project_from(None)
    assert not project_from({}).types


def test_a_listing_is_every_row_and_a_non_row_is_skipped():
    rows = envelope("list")["data"]

    read = tickets_from([*rows, "junk"], attempting="listing")

    assert [one.id for one in read] == [row["id"] for row in rows]


def test_a_listing_that_is_not_a_list_is_refused():
    with pytest.raises(UnreadableBacklog, match="rather than a list"):
        tickets_from({"id": "x"}, attempting="listing")


def test_a_ticket_with_no_id_is_refused():
    with pytest.raises(UnreadableBacklog, match="no id"):
        ticket_from({"title": "nameless"})


def test_absent_and_blank_assignees_are_both_nobody_and_a_name_is_kept():
    parent, child, orphan = tickets_from(envelope("list")["data"], attempting="listing")

    assert (parent.assignee, child.assignee, orphan.assignee) == (None, None, "someone")


def test_a_parent_is_kept_when_present_and_nothing_when_absent():
    parent, child, _ = tickets_from(envelope("list")["data"], attempting="listing")

    assert (parent.parent, child.parent) == (None, "pro-01m2aaaaaaaa")


def test_the_read_ticket_carries_criteria_tags_and_the_closed_child():
    parent = ticket_from(envelope("show-parent")["data"])

    assert [(c.title, c.done) for c in parent.acceptance] == [
        ("first thing", True),
        ("second thing", False),
    ]
    assert parent.tags == ("p0", "auth")
    assert [(c.id, c.status) for c in parent.children] == [
        ("pro-01m2bbbbbbbb", "in_progress"),
        ("pro-01m2cccccccc", "closed"),
    ]


def test_sections_keep_the_tickets_order_and_the_blank_heading_holds_the_preamble():
    parent = ticket_from(envelope("show-parent")["data"])

    assert list(parent.sections) == ["", "description", "design", "notes"]
    assert parent.sections[""] == "Text before any heading."
    assert parent.sections["design"] == "How it is built."


def test_an_empty_section_is_dropped():
    read = ticket_from({"id": "x", "sections": {"empty": "\n\n", "kept": "text\n"}})

    assert read.sections == {"kept": "text"}


def test_a_missing_blocker_is_marked_missing_and_a_closed_one_carries_its_title():
    child = ticket_from(envelope("show-child")["data"])

    assert [(b.id, b.status, b.title, b.missing) for b in child.blockers] == [
        ("pro-01m2cccccccc", "closed", "The closed one", False),
        ("pro-01m2zzzzzzzz", "", "", True),
    ]
    assert [one.id for one in child.linked] == ["pro-01m2dddddddd"]


def test_a_closed_row_carries_its_closing_instant_and_untitled_reads_as_such():
    (closed,) = tickets_from(envelope("closed")["data"], attempting="closed")

    assert closed.closed == "2026-08-02T10:00:00.000000Z"
    assert ticket_from({"id": "x"}).title == "(untitled)"


def test_graph_metrics_are_read_from_a_listing_row_and_absent_from_a_read():
    parent, child, _ = tickets_from(envelope("list")["data"], attempting="listing")
    read = ticket_from(envelope("show-parent")["data"])

    assert (parent.leverage, parent.level, parent.component) == (0, 0, 1)
    assert (child.leverage, child.coupling, child.level) == (0, 1, 1)
    assert (read.leverage, read.coupling, read.level, read.component) == (None,) * 4


def test_a_null_metric_reads_as_nothing_and_a_boolean_is_not_a_number():
    (closed,) = tickets_from(envelope("closed")["data"], attempting="closed")
    odd = ticket_from({"id": "x", "leverage": True, "level": "3"})

    assert (closed.leverage, closed.coupling) == (None, None)
    assert (odd.leverage, odd.level) == (None, None)
