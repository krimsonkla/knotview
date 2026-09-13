"""What the command resolves to serve: a saved project by name, or flags, or the working directory.

Nothing here binds a port. The resolution is a function over what was typed and what was saved, and
that is what is asserted; the server is one line after it.
"""

from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from knotview.entry import console
from knotview.entry.console import PORT, arguments, settings_for
from knotview.entry.saved_projects import SavedProjects
from knotview.values.saved_project import SavedProject
from knotview.values.unknown_project import UnknownProject


def _registry(tmp_path: Path) -> SavedProjects:
    registry = SavedProjects(tmp_path / "projects.toml")
    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7790))
    return registry


def test_no_arguments_serve_the_working_directory_on_the_default_port(tmp_path: Path):
    repository, port = settings_for(arguments([]), _registry(tmp_path), cwd=tmp_path)

    assert (repository, port) == (tmp_path, PORT)


def test_a_saved_name_supplies_both_its_path_and_its_port(tmp_path: Path):
    repository, port = settings_for(arguments(["outcry"]), _registry(tmp_path), cwd=tmp_path)

    assert (repository, port) == (tmp_path / "outcry", 7790)


def test_a_flag_beats_a_saved_port(tmp_path: Path):
    given = arguments(["outcry", "--port", "8000"])

    _, port = settings_for(given, _registry(tmp_path), cwd=tmp_path)

    assert port == 8000


def test_a_name_and_a_repository_together_are_refused(tmp_path: Path):
    """Two answers to where to read would leave the panel showing one and the command naming
    the other."""
    given = arguments(["outcry", "--repository", str(tmp_path)])

    with pytest.raises(UnknownProject, match="both"):
        settings_for(given, _registry(tmp_path), cwd=tmp_path)


def test_saving_records_the_resolved_path_and_port_under_the_name(tmp_path: Path):
    registry = _registry(tmp_path)
    given = arguments(["--repository", str(tmp_path / "new"), "--port", "7791", "--save", "new"])

    repository, port = settings_for(given, registry, cwd=tmp_path)

    assert (repository, port) == (tmp_path / "new", 7791)
    assert registry.named("new") == SavedProject(repository=tmp_path / "new", port=7791)


def test_saving_without_a_port_records_the_default(tmp_path: Path):
    registry = _registry(tmp_path)

    settings_for(arguments(["--save", "here"]), registry, cwd=tmp_path)

    assert registry.named("here") == SavedProject(repository=tmp_path, port=PORT)


def test_saving_a_saved_name_with_a_new_port_moves_it(tmp_path: Path):
    registry = _registry(tmp_path)

    settings_for(
        arguments(["outcry", "--port", "7799", "--save", "outcry"]), registry, cwd=tmp_path
    )

    assert registry.named("outcry").port == 7799


def test_a_relative_repository_is_resolved_against_the_working_directory(tmp_path: Path):
    given = arguments(["--repository", "sub"])

    repository, _ = settings_for(given, _registry(tmp_path), cwd=tmp_path)

    assert repository == (tmp_path / "sub").resolve()


def test_an_unsaved_name_is_refused(tmp_path: Path):
    with pytest.raises(UnknownProject):
        settings_for(arguments(["nowhere"]), _registry(tmp_path), cwd=tmp_path)


# --- the command itself, with the server stubbed ---


class _Backlog:
    """Stands in for the knot reader: notes where it was pointed and answers a project."""

    built: ClassVar[list] = []

    def __init__(self, *, repository: Path, knot: str) -> None:
        self.built.append((repository, knot))

    def project(self) -> SimpleNamespace:
        """A project with a name to print."""
        return SimpleNamespace(name="outcry")


def test_main_serves_the_saved_project_on_its_saved_port(tmp_path: Path, monkeypatch, capsys):
    _registry(tmp_path)
    served: list = []
    monkeypatch.setattr(console, "default_registry_path", lambda: tmp_path / "projects.toml")
    monkeypatch.setattr(console, "KnotCommand", _Backlog)
    monkeypatch.setattr(console, "panel", lambda backlog: backlog)
    monkeypatch.setattr(console.uvicorn, "run", lambda app, **bound: served.append(bound))
    monkeypatch.chdir(tmp_path)

    assert console.main(["outcry"]) == 0

    assert served[0]["port"] == 7790 and served[0]["host"] == "127.0.0.1"
    assert _Backlog.built[-1] == (tmp_path / "outcry", "knot")
    assert "7790" in capsys.readouterr().out
