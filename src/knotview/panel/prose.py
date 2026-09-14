"""Ticket text as a page reads it: knot's markdown rendered, never trusted."""

from markdown_it import MarkdownIt

# CommonMark only, with raw HTML off: a ticket body is written by whoever writes tickets, agents
# included, and a tag in it is text to show, not markup to run. Everything the renderer emits is
# its own, which is why the templates may mark its result safe, and why nothing else is.
_RENDERER = MarkdownIt("commonmark", {"html": False, "linkify": False})

# A ticket's own headings sit inside a card whose heading is the section name, so they are pushed
# two levels down: a `#` in a body becomes an h3 under the section's h2, never a rival h1.
_DEMOTE = 2


def rendered(text: str) -> str:
    """That markdown as HTML, with raw HTML escaped and headings kept below the section's.

    A plain string, marked safe by the template that uses it and nowhere else, so the one place
    page text escapes autoescaping is visible beside the filter that makes it safe to.
    """
    tokens = _RENDERER.parse(text)
    for token in tokens:
        if token.type in ("heading_open", "heading_close"):
            level = min(6, int(token.tag[1:]) + _DEMOTE)
            token.tag = f"h{level}"
    return _RENDERER.renderer.render(tokens, _RENDERER.options, {})
