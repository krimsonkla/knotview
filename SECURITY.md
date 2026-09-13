# Security

knotview binds `127.0.0.1` only, has no authentication, and shows a whole backlog to whoever can
reach it. That is the design: one reader on one machine. Do not expose it on a network or behind
a reverse proxy without adding authentication in front of it.

It never writes a ticket: every route is a GET and the only command it runs is knot's read verbs,
asserted by tests. The one file it writes is its own `projects.toml` under your configuration
home.

To report a vulnerability, open a GitHub issue describing the class of problem, or email the
address on the maintainer's GitHub profile if the details should stay private. Expect an
acknowledgement within a week.
