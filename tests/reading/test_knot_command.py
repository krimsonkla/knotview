"""The backlog read by running knot, driven through a fake knot to every branch the real one has."""

# Two tests reach the private read and the private argv builder on purpose: no public method can
# reach the refusal guard, and _spoken is the one place argv is built.
# pylint: disable=protected-access

import json
import os
from pathlib import Path

import pytest

from knotview.reading.knot_command import READS, KnotCommand, _described
from knotview.values.unreadable_backlog import UnreadableBacklog
from tests.reading.envelopes import envelope


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


def test_every_listing_read_answers_from_its_envelope(fake):
    command = fake()

    assert command.project().prefix == "pro"
    assert [one.id for one in command.live()] == [r["id"] for r in envelope("list")["data"]]
    assert [one.id for one in command.closed()] == ["pro-01m2cccccccc"]
    assert [one.id for one in command.ready()] == ["pro-01m2aaaaaaaa", "pro-01m2dddddddd"]
    assert [one.id for one in command.blocked()] == ["pro-01m2bbbbbbbb"]


def test_one_ticket_is_read_in_full_by_its_id(fake):
    child = fake().ticket("pro-01m2bbbbbbbb")

    assert child.title == "The child"
    assert child.sections == {"description": "The child does a thing."}


def test_an_unknown_id_refuses_with_knots_own_message(fake):
    with pytest.raises(UnreadableBacklog, match="no ticket matching nope"):
        fake().ticket("nope")


def test_a_show_that_answers_a_list_is_refused_as_not_a_ticket(fake):
    with pytest.raises(UnreadableBacklog, match="rather than a ticket"):
        fake().ticket("list")


def test_output_that_is_not_json_refuses_naming_the_command(fake):
    with pytest.raises(UnreadableBacklog, match="list --json printed nothing this panel can read"):
        fake(mode="junk").live()


def test_a_knot_that_hangs_refuses_after_the_patience(fake):
    with pytest.raises(UnreadableBacklog, match="did not answer within 1 seconds"):
        fake(mode="hang", patience=1).project()


def test_a_missing_binary_refuses_naming_it(tmp_path: Path):
    absent = KnotCommand(repository=tmp_path, knot=str(tmp_path / "absent"))

    with pytest.raises(UnreadableBacklog, match="absent is not on the path"):
        absent.project()


def test_a_verb_outside_the_reads_is_refused_before_anything_runs(fake):
    """Called on the private read on purpose: every public method passes a literal from READS,
    so nothing public can reach this guard. It exists for the next method somebody adds."""
    with pytest.raises(UnreadableBacklog, match="delete is not one of the reads"):
        fake()._read("delete")


def test_the_repository_is_named(fake, tmp_path: Path):
    assert fake().repository == tmp_path


def test_the_digest_is_absent_when_there_is_no_tickets_directory(fake, tmp_path: Path):
    (tmp_path / ".tickets" / "archive").rmdir()
    (tmp_path / ".tickets").rmdir()

    assert fake().digest() == "absent"


def test_the_digest_is_stable_and_moves_when_a_ticket_file_does(fake, tmp_path: Path):
    ticket = tmp_path / ".tickets" / "pro-01m2aaaaaaaa--the-parent.md"
    ticket.write_text("---\nid: pro-01m2aaaaaaaa\n---\n", encoding="utf-8")
    command = fake()
    before = command.digest()

    assert command.digest() == before
    os.utime(ticket, ns=(ticket.stat().st_atime_ns, ticket.stat().st_mtime_ns + 1_000_000))
    assert command.digest() != before


def test_the_digest_covers_the_archive(fake, tmp_path: Path):
    command = fake()
    before = command.digest()

    (tmp_path / ".tickets" / "archive" / "pro-01m2cccccccc--closed.md").write_text("x")

    assert command.digest() != before


WRITE_VERBS = (
    "create",
    "start",
    "status",
    "close",
    "reopen",
    "delete",
    "dep",
    "undep",
    "link",
    "unlink",
    "add-note",
    "edit",
    "update",
)


def test_the_reads_are_the_only_verbs_and_none_of_them_writes():
    assert set(READS).isdisjoint(WRITE_VERBS)


def test_only_the_command_module_reaches_outside_the_process():
    """The read-only guarantee is structural: knot is invoked in exactly one module, every verb it
    is handed comes from READS, and READS holds no write verb. So the guard is on who may run a
    process at all, not on which words appear in the package: "status" is also a field name."""
    source = Path(__import__("knotview").__file__).resolve().parent
    running = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*.py")
        if "subprocess" in path.read_text(encoding="utf-8")
    }
    assert running == {"reading/knot_command.py"}


def test_the_command_only_speaks_the_verb_it_was_given(fake):
    """_spoken is the one place argv is built, and it puts the READS verb first and --json last."""
    assert fake()._spoken("list", ())[1:] == ["list", "--json"]
    assert fake()._spoken("show", ("x",))[1:] == ["show", "x", "--json"]
