"""The recorder's guard and its refusal, which run without knot.

A recording that carries the recorder's home directory, scratch directory or name would be
committed into the repository with nothing failing, and a clean check that reports an issue would
make every test built on it meaningless. So the recorder refuses both, and writes nothing when it
does; these tests hold it to that without a knot binary.
"""

from pathlib import Path

import pytest

from tests.reading import record_envelopes
from tests.reading.probe import TICKETS, write_probe
from tests.reading.record_envelopes import (
    CLEAN_TICKETS,
    compared,
    destination,
    finish,
    forbidden_strings,
    leaks,
    scrubbed,
    vetted,
)

CLEAN = '{"ok": true, "data": {"issues": []}}'


def test_a_leak_is_named_by_recording_and_string():
    found = leaks({"info": '{"p": "/tmp/xyz/probe/.tickets"}', "list": "[]"}, {"/tmp/xyz", "alice"})

    assert found == [("info", "/tmp/xyz")]


def test_an_empty_or_missing_forbidden_string_is_not_searched_for():
    assert not leaks({"info": "anything"}, {"", None})


def test_a_dirty_clean_check_refuses_and_a_clean_set_passes():
    dirty = '{"ok": false, "data": {"issues": [{"code": "doc_unknown_ticket"}]}}'

    assert not vetted({"check-clean": CLEAN}, {"/tmp/x"})
    assert vetted({"check-clean": dirty}, {"/tmp/x"}) == ["check-clean reports 1 issue"]
    assert vetted({"check-clean": CLEAN, "info": "/tmp/x/a"}, {"/tmp/x"}) == [
        "info contains /tmp/x"
    ]


def test_a_refused_set_writes_nothing_and_a_clean_one_writes_everything():
    written: list[str] = []

    assert finish({"check-clean": CLEAN, "info": "/tmp/x"}, {"/tmp/x"}, written.append) == 1
    assert not written
    assert finish({"check-clean": CLEAN, "info": "ok"}, {"/tmp/x"}, written.append) == 0
    assert sorted(written) == ["check-clean", "info"]


def test_the_forbidden_strings_are_both_scratch_spellings_the_home_and_the_git_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(record_envelopes, "git_user_name", lambda: "Someone Real")
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "..")

    forbidden = forbidden_strings(str(link))

    assert forbidden == {
        str(link),
        str(link.resolve()),
        str(Path.home()),
        "Someone Real",
    }


def test_the_clean_probe_names_tickets_that_exist():
    assert set(CLEAN_TICKETS) <= set(TICKETS)


def test_a_document_that_does_not_name_its_owner_is_refused(tmp_path: Path):
    with pytest.raises(ValueError, match="is not docs/"):
        write_probe(tmp_path, {}, {"pro-01m2aaaaaaaa/loose.md": "x"})
    with pytest.raises(ValueError, match="is not docs/"):
        write_probe(tmp_path, {}, {"docs/pro-01m2aaaaaaaa/other-d1--x.md": "x"})


@pytest.mark.parametrize("order", [0, 1])
def test_every_spelling_of_the_scratch_root_becomes_the_probe_whatever_the_order(order: int):
    """On macOS the resolved spelling holds the created one; replaced shorter first, it would
    leave /private/probe. So spellings are replaced longest first, in any order given."""
    spellings = ["/tmp/x/probe", "/private/tmp/x/probe"]
    text = '{"a": "/private/tmp/x/probe/.tickets", "b": "under /tmp/x/probe/docs"}'

    recorded = scrubbed("check", text, spellings if order else spellings[::-1])

    assert '"/probe/.tickets"' in recorded and '"under /probe/docs"' in recorded
    assert "private" not in recorded


def test_a_recording_that_matches_its_committed_file_passes():
    assert not compared({"info": "a\n"}, {"info": "a\n"})


def test_a_differing_recording_is_named_with_its_diff():
    problems = compared({"info": "a\nb\n"}, {"info": "a\nc\n"})
    problem = problems[0]

    assert (
        len(problems) == 1
        and problem.startswith("info.json differs")
        and "-c" in problem
        and "+b" in problem
    )


def test_a_recording_with_no_committed_file_and_a_file_nothing_records_are_both_named():
    problems = compared({"new": "x\n"}, {"old": "y\n"})

    assert problems == [
        "new.json is recorded but not committed",
        "old.json is committed but nothing records it",
    ]


def test_a_forbidden_string_the_scrub_itself_writes_is_not_searched_for():
    """CI's git name is "probe", and every scrubbed path holds /probe: searching for it would
    refuse every recording, and --check would fail however well the recordings matched."""
    recordings = {"info": '{"cwd": "/probe", "assignee": "someone"}'}

    assert not leaks(recordings, {"probe", "someone", "/tmp/x"})
    assert leaks(recordings, {"one"}) == [("info", "one")]
    assert leaks({"info": '{"cwd": "/tmp/x/probe"}'}, {"probe", "/tmp/x"}) == [("info", "/tmp/x")]


def test_recordings_go_to_the_fixtures_unless_another_directory_is_named(tmp_path: Path):
    assert destination([]) == record_envelopes.HERE
    assert destination(["--into", str(tmp_path)]) == tmp_path
    with pytest.raises(SystemExit, match="needs a directory"):
        destination(["--into"])
    with pytest.raises(SystemExit, match="needs a directory"):
        destination(["--into", "--other"])
    with pytest.raises(SystemExit, match="takes no --into"):
        destination(["--check", "--into", str(tmp_path)])
