"""The frame every page shares: tokens, header, pinned tags, and what ships with them."""

import re
import tomllib
from pathlib import Path

from tests.panel.declared import PARENT, DeclaredBacklog

STATIC = Path("src/knotview/panel/static")


def _text(name: str) -> str:
    """One static file's text."""
    return (STATIC / name).read_text(encoding="utf-8")


def _defined(block: str) -> set[str]:
    """The custom properties a block of CSS declares."""
    return set(re.findall(r"(--[\w-]+)\s*:", block))


def _used_and_defined() -> tuple[set[str], set[str], set[str]]:
    """Every custom property the stylesheets use, and those each colour scheme defines."""
    used = set(re.findall(r"var\((--[\w-]+)", _text("panel.css") + _text("primer.css")))
    light, dark = _text("primer.css").split("@media (prefers-color-scheme: dark)", 1)
    panel_root = _defined(_text("panel.css"))
    return used, _defined(light) | panel_root, _defined(dark) | panel_root


def test_every_property_the_stylesheets_use_is_defined_for_light_and_for_dark():
    used, light, dark = _used_and_defined()

    assert used <= light, sorted(used - light)
    assert used <= dark, sorted(used - dark)


def test_the_tokens_follow_the_system_theme_and_name_their_source():
    tokens = _text("primer.css")

    assert "@media (prefers-color-scheme: dark)" in tokens
    assert "@primer/primitives@11.10.0" in tokens
    assert "data-color-mode" not in tokens


def test_the_primer_license_and_tokens_ship_and_nothing_under_docs_does():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    declared = pyproject["tool"]["setuptools"]["package-data"]["knotview"]

    assert "panel/static/*" in declared
    assert (STATIC / "primer.css").is_file() and (STATIC / "PRIMER-LICENSE").is_file()
    assert "MIT License" in _text("PRIMER-LICENSE")
    assert not any(one.startswith("docs") or "../" in one for one in declared)


def test_the_header_marks_the_current_page_and_loads_tokens_before_the_stylesheet(client):
    page = client(DeclaredBacklog()).get("/tickets").text

    assert '<a class="kv-tab" href="/tickets" aria-current="page">Tickets</a>' in page
    assert page.index("/static/primer.css") < page.index("/static/panel.css")
    assert 'href="/" aria-current' not in page


def test_a_ticket_page_sits_under_the_tickets_tab(client):
    page = client(DeclaredBacklog()).get(f"/ticket/{PARENT.id}").text

    assert 'href="/tickets" aria-current="page"' in page


def test_pinned_tags_are_their_own_control_with_a_pin_and_a_way_to_unpin(client):
    browser = client(DeclaredBacklog())
    browser.cookies.set("knotview_tags", "teams")

    header = browser.get("/tree").text.split("</header>")[0]

    assert 'class="kv-pinned"' in header
    assert 'title="Pinned tags narrow every page until unpinned"' in header
    assert "/tags?drop=teams" in header


def test_the_live_badge_keeps_its_class_when_the_poll_marks_it():
    script = _text("follow.js")

    assert 'badge.classList.toggle("stale", Boolean(stale))' in script
    assert "badge.className =" not in script


def test_hidden_wins_over_every_component_display_rule():
    assert re.search(r"\[hidden\]\s*\{\s*display:\s*none\s*!important;\s*\}", _text("panel.css"))


def test_no_page_frame_names_github(client):
    browser = client(DeclaredBacklog())

    pages = ("/", "/tickets", "/tree", "/queue/ready", "/queue/blocked", f"/ticket/{PARENT.id}")

    for path in pages:
        assert "github" not in browser.get(path).text.lower(), path
