"""Ticket text as a page reads it: knot's markdown rendered, never trusted."""

import re
from dataclasses import dataclass

from markdown_it import MarkdownIt
from markdown_it.token import Token

# CommonMark only, with raw HTML off: a ticket body is written by whoever writes tickets, agents
# included, and a tag in it is text to show, not markup to run. Everything the renderer emits is
# its own, which is why the templates may mark its result safe, and why nothing else is.
_RENDERER = MarkdownIt("commonmark", {"html": False, "linkify": False})

# A ticket's own headings sit inside a card whose heading is the section name, so they are pushed
# two levels down: a `#` in a body becomes an h3 under the section's h2, never a rival h1.
_DEMOTE = 2


@dataclass(frozen=True, kw_only=True)
class Outline:
    """One heading a document's outline links to: its level, its words, and its anchor.

    The words are plain text with the heading's markup dropped, so the template escapes them like
    any other value; only the rendered body is ever marked safe.
    """

    level: int
    text: str
    anchor: str


def rendered(text: str) -> str:
    """That markdown as HTML, with raw HTML escaped and headings kept below the section's.

    A plain string, marked safe by the template that uses it and nowhere else, so the one place
    page text escapes autoescaping is visible beside the filter that makes it safe to.
    """
    return _RENDERER.renderer.render(_walk(text, _DEMOTE), _RENDERER.options, {})


def outlined(text: str) -> tuple[str, tuple[Outline, ...]]:
    """A document's body as HTML with every heading anchored, and the outline of its top two levels.

    A document has the page to itself, under the page's own h1, so its headings are demoted once
    rather than twice. The anchors are set on the tokens, so the renderer escapes them as it does
    every attribute, and prefixed so a document's heading cannot take an id the page uses. The
    outline is built in the same pass that sets them, so a link and its target cannot disagree.
    """
    tokens = _walk(text, 1)
    taken: set[str] = set()
    headings = []
    for at, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        words = _words(tokens[at + 1])
        anchor = _unique(f"doc-{_slug(words)}", taken)
        token.attrSet("id", anchor)
        if words:
            headings.append(Outline(level=int(token.tag[1:]), text=words, anchor=anchor))
    # The top two levels the document itself uses, so one written in `##` throughout is not all
    # indented under a level it never has; a heading with no words gets an anchor but no entry.
    top = min((one.level for one in headings), default=0)
    return _RENDERER.renderer.render(tokens, _RENDERER.options, {}), tuple(
        one for one in headings if one.level <= top + 1
    )


def _walk(text: str, demote: int) -> list[Token]:
    """The parsed tokens with every heading pushed that many levels down, h6 at the most."""
    tokens = _RENDERER.parse(text)
    for token in tokens:
        if token.type in ("heading_open", "heading_close"):
            token.tag = f"h{min(6, int(token.tag[1:]) + demote)}"
    return tokens


def _words(inline: Token) -> str:
    """A heading's words as a reader sees them: its text and code, without emphasis or links."""
    return "".join(
        child.content for child in inline.children or () if child.type in ("text", "code_inline")
    ).strip()


def _slug(words: str) -> str:
    """Lowercase words joined by hyphens, or "section" for a heading with none."""
    return re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-") or "section"


def _unique(anchor: str, taken: set[str]) -> str:
    """That anchor, or the first numbered form of it not yet on the page."""
    chosen, count = anchor, 1
    while chosen in taken:
        count += 1
        chosen = f"{anchor}-{count}"
    taken.add(chosen)
    return chosen
