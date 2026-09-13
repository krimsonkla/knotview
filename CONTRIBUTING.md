# Contributing

Thanks for looking. knotview is small on purpose: a read-only panel over a knot backlog that never
parses the ticket files itself. Changes that keep it that way are welcome.

## Set up

```bash
uv sync --all-groups
```

That installs the package in editable mode with the test and lint tools. You also need
[knot](https://github.com/UniSoma/knot) on your `PATH` to run the panel and the one test that
drives the real binary; without it that test skips and everything else still runs.

## Run the checks

```bash
uv run pytest                 # the whole suite, with the coverage gate
uv run pytest --no-cov tests/panel/test_tree.py   # one file, without the gate
uv run pytest -m "not slow"   # without the real-knot fidelity test
uv run ruff check src tests
uv run pylint src tests
uv run black --check src tests
```

The coverage gate is 100 percent, line and branch, and it is enforced by `pytest`'s default
options: a full run that leaves any line or branch uncovered exits 1 even when every test passed.
A partial run (one file, one directory) always trips it, which is what `--no-cov` is for. The
gate is deliberate: the reading layer has one job, reading knot's JSON faithfully, and an
untested branch there is a branch that will drift from knot silently.

Tests are driven by envelopes recorded from a real knot under `tests/reading/envelopes/`; a fake
`knot` script replays them so the suite never needs the binary. The `slow` test replays the same
tickets through the real binary and compares shapes, so a new knot release that changes its
output fails there first. To re-record the envelopes after upgrading knot:

```bash
uv run python -m tests.reading.record_envelopes
```

## Conventions

- Commit messages follow `<type>(<scope>): <description>`, as in the history.
- Every route is a GET and nothing writes a ticket. A change that adds a write is a different
  project.
- Four-space indentation in Python, two in the templates, stylesheet and script.

The maintainer works inside a devenv shell that runs the same tools as commit hooks from a
private layer repository; that shell is not required to contribute, and the checks above are the
same ones it runs.
