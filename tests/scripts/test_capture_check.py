"""The capture script refuses a screenshot of a view with nothing in it."""

import pytest

from scripts.capture_check import EXPECTED, missing


def test_a_ready_page_with_no_rows_fails_naming_the_ready_view():
    empty = '<main class="kv-main"><p class="kv-row kv-muted">Nothing here.</p></main>'

    with pytest.raises(AssertionError, match="ready"):
        missing("ready", empty)


def test_a_ready_page_with_rows_passes():
    assert missing("ready", '<div class="kv-row" data-updated="x"></div>') is None


def test_every_captured_view_has_an_expectation():
    assert set(EXPECTED) == {
        "overview",
        "tickets",
        "tree",
        "ready",
        "blocked",
        "ticket",
        "document",
    }
