"""What a project derives from its declared values."""

from tests.panel.declared import PROJECT


def test_open_statuses_are_the_declared_ones_that_are_not_terminal():
    assert PROJECT.open_statuses == ("open", "in_progress")


def test_priorities_run_the_declared_range_highest_first():
    assert PROJECT.priorities == (0, 1, 2, 3, 4)
