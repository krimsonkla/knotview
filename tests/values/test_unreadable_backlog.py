"""The refusal carries its advice as a field and in its message."""

from knotview.values.unreadable_backlog import UnreadableBacklog


def test_the_message_and_the_advice_are_both_kept_and_joined():
    refusal = UnreadableBacklog("could not read", advice="point it at a project")

    assert (refusal.message, refusal.advice) == ("could not read", "point it at a project")
    assert str(refusal) == "could not read. point it at a project"
    assert refusal.code is None
