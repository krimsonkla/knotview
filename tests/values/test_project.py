"""What a project derives from its declared values."""

from tests.panel.declared import PROJECT


def test_open_statuses_are_the_declared_ones_that_are_not_terminal():
    assert PROJECT.open_statuses == ("open", "in_progress")


def test_priorities_run_the_declared_range_highest_first():
    assert PROJECT.priorities == (0, 1, 2, 3, 4)


def test_a_status_is_terminal_when_the_project_says_so():
    assert PROJECT.is_terminal("closed") and not PROJECT.is_terminal("open")
