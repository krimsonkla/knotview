"""The backlog read by running knot, driven through a fake knot to every branch the real one has."""

import json

import pytest

from knotview.reading.knot_command import _described
from knotview.values.unreadable_backlog import UnreadableBacklog


def test_a_clean_check_reports_no_issues(fake):
    assert fake(check="clean").integrity() == ()


def test_a_check_with_issues_reports_each_as_a_line_naming_the_ticket_and_the_code(fake):
    """This is the path knot's ok:false verdict used to close: the overview refused to render."""
    (line,) = fake(check="issues").integrity()

    assert line.startswith("pro-01m2bbbbbbbb unknown_id: unknown id")


def test_a_failed_scan_with_no_issues_is_refused_rather_than_read_as_clean(fake):
    with pytest.raises(UnreadableBacklog, match="was refused"):
        fake(check="empty").integrity()


def test_a_refused_check_is_refused(fake):
    with pytest.raises(UnreadableBacklog, match="no ticket matching"):
        fake(check="error").integrity()


def test_an_issue_line_carries_every_id_the_code_the_message_and_the_path():
    line = _described(
        {
            "ids": ["a", "b"],
            "code": "terminal_outside_archive",
            "message": "misplaced",
            "path": "/p",
        }
    )

    assert line == "a b terminal_outside_archive: misplaced (/p)"


def test_an_issue_that_is_only_text_passes_through():
    assert _described("a plain line") == "a plain line"


def test_an_issue_shaped_unexpectedly_is_shown_as_it_was_given():
    assert _described({"surprise": 1}) == json.dumps({"surprise": 1})
    assert _described(42) == "42"
