"""The live digest follows documents kept outside the tickets directory, and only once inside it."""

import os
from pathlib import Path

import pytest

from knotview.reading.knot_command import Where
from tests.panel.declared import PROJECT


def written(path: Path, text: str = "a document\n") -> Path:
    """A markdown file at that path, its directories made."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def moved(command, path: Path) -> bool:
    """Whether writing that file again, a moment later, changes the digest."""
    before = command.digest()
    written(path, "changed\n")
    stamp = path.stat().st_mtime_ns + 1_000_000_000
    os.utime(path, ns=(stamp, stamp))
    return command.digest() != before


@pytest.mark.parametrize("folder", ["docs", ".tickets-docs"])
def test_a_document_outside_the_tickets_directory_moves_the_digest(
    fake, tmp_path, monkeypatch, folder
):
    monkeypatch.setenv("KNOTVIEW_FAKE_DOCS", str(tmp_path / folder))
    document = written(tmp_path / folder / "pro-1" / "pro-1-d1--a.md")

    assert moved(fake(), document)


def test_documents_in_the_default_place_are_counted_once(fake, tmp_path, monkeypatch):
    written(tmp_path / ".tickets" / "docs" / "pro-1" / "pro-1-d1--a.md")
    inside = fake().digest()
    monkeypatch.setenv("KNOTVIEW_FAKE_DOCS", str(tmp_path / "nowhere"))

    assert fake().digest() == inside


def test_a_docs_directory_that_does_not_exist_leaves_the_tickets_digest(
    fake, tmp_path, monkeypatch
):
    written(tmp_path / ".tickets" / "pro-1--a.md")
    alone = fake().digest()
    monkeypatch.setenv("KNOTVIEW_FAKE_DOCS", str(tmp_path / "missing"))

    assert fake().digest() == alone


def test_a_knot_that_states_no_docs_path_or_root_gets_knots_own_defaults():
    where = Where.of(PROJECT)

    assert where.docs == Path(PROJECT.tickets_path) / "docs"
    assert where.root == Path(PROJECT.tickets_path).parent
