# knotview

A read-only panel over a [knot](https://github.com/UniSoma/knot) backlog, shaped by the project's own
configuration rather than by this panel's idea of one.

knotview exists because of knot. [knot](https://github.com/UniSoma/knot), by
[UniSoma](https://github.com/UniSoma), is the ticket tracker this panel reads: markdown tickets
with YAML frontmatter that live in the repository beside the code, a dependency graph with ready
and blocked queues, acceptance criteria that gate closing, and a JSON protocol on every command
built for handing work to an agent. Everything this panel shows is knot's data and knot's
vocabulary; the panel adds pages, filters, a tree and a live view, and never a second copy of the
schema. If you have not met knot, start there: its README explains the design, and `knot serve`
ships a panel of its own that this one grew out of wanting more of.

## Two ways to run it

**Without devenv**, which is how a user of the panel runs it. You need Python 3.12 or later,
[knot](https://github.com/UniSoma/knot) on your `PATH` (or `--knot /path/to/knot`), and a
directory that is a knot project: one holding `.knot.edn` or `.tickets/`. knotview never reads the
ticket files itself; it runs `knot ... --json` in the project and shows what knot answers.

```bash
uv tool install git+https://github.com/krimsonkla/knotview
knotview --repository /path/to/a/knot/project --port 7778
```

or from a checkout, `uv sync --all-groups` then `uv run knotview --repository /path/to/a/knot/project`.
A plain `pip install .` works too and installs the `knotview` command.

**With devenv**, which is how the panel is developed. The [devenv](https://devenv.sh) shell
supplies Python, uv, knot, the formatters and the commit hooks, and `devenv up` serves the panel
over this repository's own backlog, which is the fixture the panel is developed against:

```bash
devenv shell          # everything on PATH, uv sync already run
devenv up             # serves http://127.0.0.1:7778/ over this repository
KNOTVIEW_REPOSITORY=/path/to/another/project KNOTVIEW_PORT=7779 devenv up
```

Inside the shell, `knotview`, `pytest` and `prek run --all-files` all work as they do in
[CONTRIBUTING.md](CONTRIBUTING.md). The shell pulls its hooks and knot from a private layer
repository, so it evaluates only for the maintainer today; nothing in the package or the tests
depends on it, and the uv path above runs the same checks.

Either way, open <http://127.0.0.1:7778/>. The panel binds loopback only and has no
authentication, because it shows a whole backlog to whoever can reach it; do not put it on a
network.

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
  directions of its graph, its links, its notes, and knot's own dependency tree drawn all the way
  down, with a missing dependency shown as such.
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
