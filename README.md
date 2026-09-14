# knotview

A read-only panel over a [knot](https://github.com/UniSoma/knot) backlog, shaped by the project's own
configuration rather than by this panel's idea of one.

## Prerequisites

- Python 3.12 or later.
- [knot](https://github.com/UniSoma/knot) on your `PATH`. knotview never reads the ticket files
  itself; it runs `knot ... --json` in the project and shows what knot answers, so without knot
  there is nothing to show. If knot lives somewhere unusual, pass `--knot /path/to/knot`.
- A directory that is a knot project: it holds `.knot.edn` or `.tickets/`.

## Install and run

With [uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/krimsonkla/knotview
knotview --repository /path/to/a/knot/project --port 7778
```

or from a checkout, `uv sync` then `uv run knotview --repository /path/to/a/knot/project`. A plain
`pip install .` works too and installs the `knotview` command.

Then open <http://127.0.0.1:7778/>. The panel binds loopback only and has no authentication,
because it shows a whole backlog to whoever can reach it; do not put it on a network.

Two projects open at once is the ordinary case, and each needs its own port, so a project's path
and port can be saved under a name and served by that name afterwards:

```bash
knotview --repository ~/git/one --port 7778 --save one
knotview --repository ~/git/two --port 7779 --save two
knotview one
knotview two
```

A flag still wins for one run, so `knotview one --port 8000` serves the saved path on another
port without changing what is saved. The names live in `~/.config/knotview/projects.toml`, or under
`XDG_CONFIG_HOME` where that is set, as plain TOML a person can edit; they are saved per machine
rather than in the project, because which port is free and where a checkout lives are facts about
the machine.

It reads. Nothing here writes a ticket, and the backlog stays driven by whatever drives it.

## The maintainer's environment

This repository is developed inside a [devenv](https://devenv.sh) shell that supplies knot, the
formatters and the commit hooks from a private layer repository, so `devenv shell` will not
evaluate for anyone without access to it. Nothing above depends on it: the package, the tests and
the linters all run from a plain `uv sync --all-groups`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## What it shows

- **Overview.** The backlog counted by type, by status and by priority, every one of them read from
  the project's own declared values, so a type nobody has filed yet still appears. Beside it: knot's
  ready and blocked queues, what is assigned to nobody, the parents, the recently closed, and whatever
  the project's own integrity check reports.
- **Tickets.** Every ticket, filtered by type, status, priority, mode, assignee or tag, ordered by
  priority, update, creation, title or id, searched by id, title or tag, with the closed ones included
  on request. Every filter is a query parameter, so a view is a link somebody can keep.
- **Attention.** What knot's own primer reports and nothing else does: the tickets in progress
  with every criterion ticked, which are ready to close, and the ones in progress for two weeks
  without a change, which are stale. Both come from `knot prime`, so the panel agrees with the CLI.
- **Tree.** What is filed under what, with each parent's children counted and its own acceptance
  criteria counted separately, and the tickets filed under nothing listed at the bottom, because that
  is where work goes missing.
- **Ticket.** The sections as the ticket wrote them, its acceptance criteria with what is met, both
  directions of its graph, its links and its notes.
- **Live.** A one-way stream says when the backlog changed and the page reloads itself. The stream
  carries a digest rather than markup, so what you see after a change is what a fresh visit shows.

## How it reads

Through `knot ... --json`, never by parsing `.tickets` directly. knot owns that schema; a second parser
here would be a second schema, and it would drift on the first release that adds a field. The commands
it runs are declared in one constant and every one of them is a read.

## Why not `knot serve`

knot ships its own panel, and it is good at what it does: three fixed groups, in progress over ready
over blocked, expanded inline. What it does not do is navigate a project's own types, filter, show the
closed work, draw the shape of what is filed under what, or follow changes without being asked. That is
what this adds.

## Licence

MIT. See [LICENSE](LICENSE).
