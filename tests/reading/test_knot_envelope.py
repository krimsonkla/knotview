"""Reading knot's answer shape into this panel's values, from envelopes knot actually emitted."""

import pytest

from knotview.reading.knot_envelope import (
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
