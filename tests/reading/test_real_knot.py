"""The real knot against the recorded envelopes, so the fixtures cannot rot silently.

Fidelity only: every source line is covered by the fake. This writes ticket files directly rather
than through knot's write verbs, because this repository's ticket-discipline hook blocks bare knot
writes and the fixtures were recorded the same way.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from knotview.reading.knot_command import KnotCommand
from knotview.values.missing_document import MissingDocument
from knotview.values.missing_ticket import MissingTicket
from knotview.values.unreadable_backlog import UnreadableBacklog
from tests.reading.envelopes import RECORDINGS, envelope
from tests.reading.probe import DOCUMENTS, TICKETS, write_probe
from tests.reading.record_envelopes import write_faults

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(shutil.which("knot") is None, reason="knot is not on PATH"),
]


@pytest.fixture(name="probe", scope="module")
def probe_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A knot project holding the same tickets and documents the fixtures were recorded from."""
    root = tmp_path_factory.mktemp("probe")
    write_probe(root, TICKETS, DOCUMENTS)
    return root


def raw(probe: Path, command: str, arguments: tuple[str, ...]) -> dict:
    """One envelope straight from the binary, spoken as the reader speaks it."""
    spoken = [*command.split(), "--json", *(["--", *arguments] if arguments else [])]
    answer = subprocess.run(
        ["knot", *spoken], cwd=probe, capture_output=True, text=True, check=False
    )
    return json.loads(answer.stdout)


def shape(value: object) -> object:
    """Key sets and list shapes, with values dropped, so timestamps and paths do not compare."""
    if isinstance(value, dict):
        return {key: shape(held) for key, held in sorted(value.items())}
    if isinstance(value, list):
        return [shape(held) for held in value]
    return type(value).__name__


def agrees(recorded: object, actual: object) -> list[str]:
    """Where the binary's shape departs from the recording, as paths; empty when it agrees.

    Additive: knot documents that new keys arrive without a version bump, so a key the binary
    adds is not a departure, while a recorded key that is missing or changed type is. A value the
    recording holds as a string may come back null, since the probe's git identity is the
    recorder's and a runner has none.
    """
    return list(_departures(recorded, actual, ""))


def _departures(recorded: object, actual: object, at: str):
    if isinstance(recorded, dict):
        yield from _mapping_departures(recorded, actual, at)
    elif isinstance(recorded, list):
        yield from _list_departures(recorded, actual, at)
    elif recorded != actual and not (recorded == "str" and actual == "NoneType"):
        yield f"{at}: {actual} where {recorded} was recorded"


def _mapping_departures(recorded: dict, actual: object, at: str):
    if not isinstance(actual, dict):
        yield f"{at}: {type(actual).__name__} where a mapping was recorded"
        return
    for key, held in recorded.items():
        if key not in actual:
            yield f"{at}.{key}: missing"
        else:
            yield from _departures(held, actual[key], f"{at}.{key}")


def _list_departures(recorded: list, actual: object, at: str):
    if not isinstance(actual, list):
        yield f"{at}: {type(actual).__name__} where a list was recorded"
        return
    for index, held in enumerate(recorded[: len(actual)]):
        yield from _departures(held, actual[index], f"{at}[{index}]")
    if len(actual) != len(recorded):
        yield f"{at}: {len(actual)} entries where {len(recorded)} were recorded"


@pytest.mark.parametrize(("name", "command", "arguments"), RECORDINGS)
def test_the_binary_still_emits_the_recorded_shape(
    probe: Path, name: str, command: str, arguments: tuple[str, ...]
):
    assert not agrees(shape(envelope(name)), shape(raw(probe, command, arguments)))


def test_the_reader_over_the_binary_agrees_with_the_reader_over_the_recording(probe: Path):
    command = KnotCommand(repository=probe)

    assert [one.id for one in command.live()] == [row["id"] for row in envelope("list")["data"]]
    assert [one.id for one in command.ready()] == ["pro-01m2aaaaaaaa", "pro-01m2dddddddd"]
    assert [one.id for one in command.blocked()] == ["pro-01m2bbbbbbbb"]
    assert [one.id for one in command.closed()] == ["pro-01m2cccccccc"]
    child = command.ticket("pro-01m2bbbbbbbb")
    assert [b.id for b in child.blockers] == ["pro-01m2cccccccc", "pro-01m2zzzzzzzz"]
    parent = command.ticket("pro-01m2aaaaaaaa")
    assert list(parent.sections) == ["", "description", "design", "notes"]
    (issue,) = command.integrity()
    assert issue.text.startswith("pro-01m2bbbbbbbb unknown_id:") and issue.document_ids == ()
    with pytest.raises(UnreadableBacklog, match="no ticket matching -x"):
        command.ticket("-x")
    assert command.digest() != "absent"
    listed = command.documents("pro-01m2aaaaaaaa")
    recorded = envelope("document-list")["data"]["documents"]
    assert [(one.id, one.created) for one in listed] == [
        (row["id"], row["created"]) for row in recorded
    ]
    # knot resolves the start of an id and answers with the whole one.
    assert command.document("pro-01m2aaaaaaaa-d7").id == "pro-01m2aaaaaaaa-d7spec"
    with pytest.raises(MissingDocument):
        command.document("pro-01m2aaaaaaaa-dnope")
    with pytest.raises(MissingTicket):
        command.documents("nope")


def test_a_ticket_file_with_no_id_leaves_the_rest_of_the_backlog_readable(tmp_path: Path):
    """The file is reported by the check, as missing_required_field, rather than hiding the
    backlog behind a refusal."""
    write_probe(tmp_path, TICKETS, DOCUMENTS)
    (tmp_path / ".tickets" / "pro-01m2xxxxxxxx--no-id.md").write_text(
        "---\ntitle: No id\nstatus: open\ntype: task\npriority: 2\n---\nBody\n",
        encoding="utf-8",
    )
    command = KnotCommand(repository=tmp_path)

    assert "pro-01m2aaaaaaaa" in [one.id for one in command.live()]
    assert command.ready() and "pro-01m2bbbbbbbb" in [one.id for one in command.blocked()]
    assert "missing_required_field" in [
        issue.text.split(":")[0].split()[-1] for issue in command.integrity()
    ]


def test_the_binary_reports_the_recorded_document_issues_the_way_the_reader_reads_them(
    tmp_path: Path,
):
    """The check-documents recording against the binary, over the probe it was recorded from:
    the same codes in the same order, the documents linked, the ticket's id not."""
    write_faults(tmp_path)

    orphan, memo, legacy = KnotCommand(repository=tmp_path).integrity()

    assert orphan.document_ids == ("pro-01m2zzzzzzzz-d1x",)
    assert memo.document_ids == ("pro-01m2aaaaaaaa-d5memo",)
    assert memo.shown == ".tickets/docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d5memo--memo.md"
    assert not legacy.document_ids and "legacy_documents_section" in legacy.text
