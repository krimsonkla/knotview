"""The probe project the envelopes are recorded from and the fidelity test runs against.

One definition, so the recorder and the fidelity test cannot drift apart. Tickets and documents are
written as files rather than through knot's write verbs, because this repository's
ticket-discipline hook blocks bare knot writes, and because a document knot creates gets a random
id and the current time, which no fixed recording can hold. Later stories extend the documents and
pass their own .knot.edn. Imports neither pytest nor knotview, so the recorder stays a script.
"""

import subprocess
from pathlib import Path

# The probe's config: the prefix, so the ids match and the name stays null as recorded, and a
# requirement that a ticket own a spec and a plan before it enters in_progress. The in-progress
# child owns only a spec and the orphan owns nothing, so the recordings carry real cases of a ticket
# lacking what its status requires; knot enforces the rule only when a ticket moves, so neither is
# reported by check.
PROBE_CONFIG = '{:prefix "pro" :required-docs {"in_progress" ["spec" "plan"]}}\n'

TICKETS = {
    "pro-01m2aaaaaaaa--the-parent.md": """---
id: pro-01m2aaaaaaaa
title: The parent
status: open
type: epic
priority: 1
mode: hitl
created: '2026-09-01T10:00:00.000000Z'
updated: '2026-09-02T10:00:00.000000Z'
acceptance:
- {title: first thing, done: true}
- {title: second thing, done: false}
tags:
- p0
- auth
---
Text before any heading.

## Description
What the parent is for.

## Design
How it is built.

## Notes

**2026-09-02T10:00:00.000000Z**

A note on the parent.
""",
    "pro-01m2bbbbbbbb--the-child.md": """---
id: pro-01m2bbbbbbbb
title: The child
status: in_progress
type: task
priority: 2
mode: afk
created: '2026-09-03T10:00:00.000000Z'
updated: '2026-09-04T10:00:00.000000Z'
assignee: ''
parent: pro-01m2aaaaaaaa
deps:
- pro-01m2cccccccc
- pro-01m2zzzzzzzz
links:
- pro-01m2dddddddd
---

## Description
The child does a thing.
""",
    "pro-01m2dddddddd--the-orphan.md": """---
id: pro-01m2dddddddd
title: The orphan
status: open
type: bug
priority: 3
mode: hitl
created: '2026-09-05T10:00:00.000000Z'
updated: '2026-09-05T10:00:00.000000Z'
assignee: someone
links:
- pro-01m2bbbbbbbb
---

## Description
Filed under nothing.
""",
    "archive/pro-01m2cccccccc--the-closed-one.md": """---
id: pro-01m2cccccccc
title: The closed one
status: closed
type: chore
priority: 4
mode: hitl
created: '2026-08-01T10:00:00.000000Z'
updated: '2026-08-02T10:00:00.000000Z'
closed: '2026-08-02T10:00:00.000000Z'
parent: pro-01m2aaaaaaaa
---

## Description
Done and archived.
""",
}

# Documents by path under .tickets/. The parent's plan has an id that sorts before its spec's,
# though it was created later and its title sorts after, so no ordering a reader needs is inherited
# from knot's id order by accident. The live child and the archived child own one each, so every
# listing carries a row with doc_types; the orphan owns none.
DOCUMENTS = {
    "docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d2plan--rollout-plan.md": """---
id: pro-01m2aaaaaaaa-d2plan
ticket: pro-01m2aaaaaaaa
title: Rollout plan
type: plan
created: '2026-09-06T10:00:00.000000Z'
updated: '2026-09-06T10:00:00.000000Z'
---

## Steps

One, then two.
""",
    "docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d7spec--design-spec.md": """---
id: pro-01m2aaaaaaaa-d7spec
ticket: pro-01m2aaaaaaaa
title: Design spec
type: spec
created: '2026-09-02T10:00:00.000000Z'
updated: '2026-09-02T10:00:00.000000Z'
---

## Design

A *spec* with a [link](https://example.test).

| a | b |
|---|---|
| 1 | 2 |
""",
    "docs/pro-01m2bbbbbbbb/pro-01m2bbbbbbbb-d4spec--child-spec.md": """---
id: pro-01m2bbbbbbbb-d4spec
ticket: pro-01m2bbbbbbbb
title: Child spec
type: spec
created: '2026-09-04T10:00:00.000000Z'
updated: '2026-09-04T10:00:00.000000Z'
---

The child's own spec.
""",
    "docs/pro-01m2cccccccc/pro-01m2cccccccc-d9note--closing-notes.md": """---
id: pro-01m2cccccccc-d9note
ticket: pro-01m2cccccccc
title: Closing notes
type: other
created: '2026-08-02T10:00:00.000000Z'
updated: '2026-08-02T10:00:00.000000Z'
---

Written when it closed.
""",
}


def write_probe(
    root: Path, tickets: dict[str, str], documents: dict[str, str], knot_edn: str = PROBE_CONFIG
) -> None:
    """Lay out a knot project at root: the config, the tickets, and the documents they own.

    A document is written only when its owner is among the tickets written, so a probe holding a
    subset of the tickets never orphans a document, which knot's check reports as an error. A
    document whose path does not name its owner, as
    docs/<ticket-id>/<ticket-id>-d<suffix>--<slug>.md does, is refused with ValueError before
    anything is written, rather than dropped unnoticed.
    """
    for name in documents:
        where = Path(name)
        if where.parts[:1] != ("docs",) or not where.name.startswith(f"{where.parent.name}-d"):
            raise ValueError(f"{name} is not docs/<ticket-id>/<ticket-id>-d<suffix>--<slug>.md")
    subprocess.run(["knot", "init"], cwd=root, check=True, capture_output=True)
    (root / ".knot.edn").write_text(knot_edn, encoding="utf-8")
    owners = {Path(name).name.split("--")[0] for name in tickets}
    written = dict(tickets)
    written.update(
        (name, text) for name, text in documents.items() if Path(name).parent.name in owners
    )
    for name, text in written.items():
        path = root / ".tickets" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
