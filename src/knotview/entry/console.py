"""The command: point the panel at a project and serve it on loopback."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from knotview.panel.app import panel
from knotview.entry.saved_projects import SavedProjects, default_registry_path
from knotview.reading.knot_command import KnotCommand
from knotview.values.saved_project import SavedProject
from knotview.values.unknown_project import UnknownProject
from knotview.values.unreadable_backlog import UnreadableBacklog

# Loopback, and not a default that can be overridden into something else. This panel shows a whole
# backlog with no authentication of any kind, which is fine for one reader on one machine and is not
# fine on a network. An address is therefore not a flag.
ADDRESS = "127.0.0.1"

# The port, which is a flag because two projects open at once is the ordinary case. Deliberately not
# knot's own 7777, so this can run beside `knot serve` rather than fighting it for the port.
PORT = 7778


def arguments(given: Sequence[str]) -> argparse.Namespace:
    """What was asked for, parsed in one place so nothing else reads the command line."""
    parser = argparse.ArgumentParser(
        prog="knotview",
        description="A read-only panel over a knot backlog, on loopback.",
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="a project saved with --save, which supplies its repository and its port",
    )
    parser.add_argument(
        "--repository",
        type=Path,
        help="the project to read, which defaults to the working directory",
    )
    parser.add_argument(
        "--port", type=int, help=f"the port to bind (default {PORT}, or the saved one)"
    )
    parser.add_argument(
        "--save",
        metavar="NAME",
        help="remember this repository and port under that name, for next time",
    )
    parser.add_argument(
        "--knot", default="knot", help="the knot command to run, for an unusual installation"
    )
    return parser.parse_args(given)


def settings_for(asked: argparse.Namespace, saved: SavedProjects, *, cwd: Path) -> tuple[Path, int]:
    """The repository and the port to serve, from what was typed and what was saved.

    A flag beats a saved setting, and a saved setting beats the default, so a name saved once needs
    nothing typed again and can still be overridden for one run. A name and a repository together
    are refused rather than one quietly winning: two answers to where to read would leave the panel
    showing one and the command naming the other.
    """
    if asked.project is not None and asked.repository is not None:
        raise UnknownProject(
            "both a saved project and a repository were given",
            advice="name the saved project, or point at a repository, not both",
        )
    remembered = None if asked.project is None else saved.named(asked.project)
    repository = _repository(asked.repository, remembered, cwd)
    port = (
        asked.port if asked.port is not None else (PORT if remembered is None else remembered.port)
    )
    if asked.save is not None:
        saved.save(asked.save, SavedProject(repository=repository, port=port))
    return repository, port


def _repository(given: Path | None, remembered: SavedProject | None, cwd: Path) -> Path:
    """The repository to read: the flag, the saved one, or the working directory."""
    if given is not None:
        return (cwd / given.expanduser()).resolve()
    return cwd if remembered is None else remembered.repository


def main(given: Sequence[str] | None = None) -> int:
    """Serve the panel over one project, or say why it cannot be read.

    The project is checked before the server binds. A panel that bound and then answered every page
    with a refusal would look like it was working, and the mistake this catches is the ordinary one:
    being pointed at a directory that is not a knot project.
    """
    asked = arguments(sys.argv[1:] if given is None else given)
    try:
        repository, port = settings_for(
            asked, SavedProjects(default_registry_path()), cwd=Path.cwd().resolve()
        )
        backlog = KnotCommand(repository=repository, knot=asked.knot)
        project = backlog.project()
    except (UnknownProject, UnreadableBacklog) as refusal:
        # The two refusals a person can act on, said in one line each rather than as a stack.
        print(f"knotview: {refusal.message}.", file=sys.stderr)
        print(f"knotview: {refusal.advice}.", file=sys.stderr)
        return 1
    print(f"knotview — http://{ADDRESS}:{port}/  reading {project.name} at {repository}")
    uvicorn.run(panel(backlog), host=ADDRESS, port=port, log_level="warning")
    return 0
