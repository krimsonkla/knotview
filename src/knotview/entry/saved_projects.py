"""The projects saved under a name, in one file the person can read and edit."""

import os
import tomllib
from pathlib import Path

from knotview.values.saved_project import SavedProject
from knotview.values.unknown_project import UnknownProject

# Where the file lives unless the environment says otherwise: the XDG place for a person's own
# configuration, which is what these are.
CONFIGURATION = Path("knotview") / "projects.toml"


def default_registry_path(environment: dict[str, str] | None = None) -> Path:
    """The file this machine's saved projects are kept in, under the person's configuration home."""
    read = os.environ if environment is None else environment
    home = Path(read.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return home / CONFIGURATION


class SavedProjects:
    """Reads and writes the file, one table per name, each holding a repository and a port.

    TOML, and written by hand rather than through a library, because the shape is three lines a
    table and a person editing it should find exactly what they would have written. Names are quoted
    table headers, so a name is any text rather than only what TOML lets stand bare.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def names(self) -> tuple[str, ...]:
        """Every saved name, in the order they were saved."""
        return tuple(self._read())

    def named(self, name: str) -> SavedProject:
        """The project saved under that name, or a refusal naming the ones that were."""
        saved = self._read()
        if name not in saved:
            known = ", ".join(saved) if saved else "nothing saved yet"
            raise UnknownProject(
                f"no project is saved as {name!r}",
                advice=f"saved: {known}; save one with knotview --repository PATH --save NAME",
            )
        entry = saved[name]
        try:
            return SavedProject(repository=Path(entry["repository"]), port=int(entry["port"]))
        except (KeyError, TypeError, ValueError) as broken:
            raise UnknownProject(
                f"the project saved as {name!r} in {self._path} is missing a repository or a port",
                advice="give it both, or save it again with knotview --repository PATH --save NAME",
            ) from broken

    def save(self, name: str, project: SavedProject) -> None:
        """Record that project under that name, replacing what the name held before."""
        if not name.strip():
            raise UnknownProject(
                "a project was given no name", advice="save it as knotview --save NAME"
            )
        saved = self._read()
        saved[name] = {"repository": str(project.repository), "port": project.port}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(_rendered(saved), encoding="utf-8")

    def _read(self) -> dict[str, dict]:
        """The file as tables by name, or nothing where no file exists yet."""
        if not self._path.is_file():
            return {}
        try:
            return tomllib.loads(self._path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as broken:
            raise UnknownProject(
                f"{self._path} is not valid TOML: {broken}",
                advice="fix the file by hand, or delete it and save the projects again",
            ) from broken


def _rendered(saved: dict[str, dict]) -> str:
    """The file as a person would write it: a quoted table per name, its two settings beneath."""
    lines = [
        "# Projects knotview serves by name. Edit freely; knotview --save NAME writes here.",
        "",
    ]
    for name, entry in saved.items():
        lines += [
            f'["{_escaped(name)}"]',
            f'repository = "{_escaped(entry["repository"])}"',
            f"port = {entry['port']}",
            "",
        ]
    return "\n".join(lines)


def _escaped(text: str) -> str:
    """That text inside a TOML basic string."""
    return text.replace("\\", "\\\\").replace('"', '\\"')
