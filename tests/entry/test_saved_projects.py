"""A project's path and port, saved once under a name so the command needs neither again.

Saved per machine rather than in the project, because both are machine-local facts: which port is
free here, and where this checkout happens to be. A file in the project would travel to a machine
where the port is taken and the path is wrong.
"""

from pathlib import Path

import pytest

from knotview.entry.saved_projects import SavedProjects, default_registry_path
from knotview.values.saved_project import SavedProject
from knotview.values.unknown_project import UnknownProject


def _registry(tmp_path: Path) -> SavedProjects:
    return SavedProjects(tmp_path / "config" / "knotview" / "projects.toml")


def test_a_saved_project_is_read_back_under_its_name(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7778))

    assert registry.named("outcry") == SavedProject(repository=tmp_path / "outcry", port=7778)


def test_saving_creates_the_file_and_its_directories(tmp_path: Path):
    registry = _registry(tmp_path)

    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7778))

    assert (tmp_path / "config" / "knotview" / "projects.toml").is_file()


def test_several_projects_keep_their_own_ports(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7778))
    registry.save("other", SavedProject(repository=tmp_path / "other", port=7779))

    assert registry.named("other").port == 7779
    assert registry.named("outcry").port == 7778


def test_saving_a_name_again_replaces_it(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7778))
    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7790))

    assert registry.named("outcry").port == 7790
    assert (tmp_path / "config" / "knotview" / "projects.toml").read_text().count('["outcry"]') == 1


def test_the_file_keeps_the_order_saved(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.save("zeta", SavedProject(repository=tmp_path / "z", port=1))
    registry.save("alpha", SavedProject(repository=tmp_path / "a", port=2))

    written = (tmp_path / "config" / "knotview" / "projects.toml").read_text()
    assert written.index('["zeta"]') < written.index('["alpha"]')


def test_a_name_nobody_saved_is_refused_naming_the_ones_that_were(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7778))

    with pytest.raises(UnknownProject) as refused:
        registry.named("nowhere")

    assert "nowhere" in refused.value.message and "outcry" in refused.value.advice


def test_a_name_asked_of_no_file_at_all_is_refused_with_how_to_save_one(tmp_path: Path):
    with pytest.raises(UnknownProject) as refused:
        _registry(tmp_path).named("outcry")

    assert "--save" in refused.value.advice


def test_the_file_is_toml_a_person_can_read_and_edit(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.save("outcry", SavedProject(repository=tmp_path / "outcry", port=7778))

    written = (tmp_path / "config" / "knotview" / "projects.toml").read_text(encoding="utf-8")

    assert '["outcry"]' in written and "port = 7778" in written


def test_a_name_with_a_quote_in_it_survives_the_round_trip(tmp_path: Path):
    """Names are quoted table headers, so a name is any text rather than only a bare key."""
    registry = _registry(tmp_path)
    registry.save('my "thing"', SavedProject(repository=tmp_path / "t", port=7780))

    assert registry.named('my "thing"').port == 7780


def test_a_blank_name_is_refused(tmp_path: Path):
    with pytest.raises(UnknownProject, match="no name"):
        _registry(tmp_path).save("  ", SavedProject(repository=tmp_path / "t", port=7780))


def test_a_port_outside_the_range_a_port_can_be_is_refused(tmp_path: Path):
    with pytest.raises(UnknownProject, match="not a port"):
        SavedProject(repository=tmp_path / "t", port=70000)


# --- where the file lives ---


def test_the_registry_lives_under_the_configuration_home_the_environment_names(tmp_path: Path):
    assert default_registry_path({"XDG_CONFIG_HOME": str(tmp_path)}) == (
        tmp_path / "knotview" / "projects.toml"
    )


def test_the_registry_lives_under_the_home_dot_config_otherwise():
    assert default_registry_path({}) == Path.home() / ".config" / "knotview" / "projects.toml"


def _written(tmp_path: Path, text: str) -> SavedProjects:
    """A registry whose file already holds that text, as a person editing it might leave it."""
    path = tmp_path / "config" / "knotview" / "projects.toml"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return SavedProjects(path)


def test_a_file_that_is_not_toml_is_refused_with_its_path_and_advice(tmp_path: Path):
    registry = _written(tmp_path, "[x\n")

    with pytest.raises(UnknownProject, match="is not valid TOML") as refused:
        registry.named("outcry")

    assert "delete it" in refused.value.advice


def test_a_saved_project_missing_a_field_is_refused_rather_than_a_key_error(tmp_path: Path):
    registry = _written(tmp_path, '["outcry"]\nport = 7778\n')

    with pytest.raises(UnknownProject, match="missing a repository or a port"):
        registry.named("outcry")
