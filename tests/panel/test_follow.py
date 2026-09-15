"""The page-side script, checked for the shape the templates rely on.

There is no JavaScript runtime in the toolchain, so this reads the file the panel serves. It
proves the selectors are present and that text is assigned in one place, inside the stamp loop
behind the parse guard; it does not prove the rewrite works, which is verified by hand in a
browser and recorded on the ticket.
"""

from knotview.panel.app import HERE

FOLLOW = (HERE / "static" / "follow.js").read_text(encoding="utf-8")


def test_stamps_are_selected_by_class_and_distances_are_never_rewritten():
    assert 'querySelectorAll("time.stamp[datetime]")' in FOLLOW
    assert 'querySelectorAll("time.ago[datetime]")' in FOLLOW
    block = FOLLOW[FOLLOW.index("// Instants in the reader") :]
    assert block.count("textContent = ") == 1
    stamp_loop = block[block.index('"time.stamp[datetime]"') : block.index('"time.ago[datetime]"')]
    assert "isNaN(when.getTime())" in stamp_loop
    assert stamp_loop.index("isNaN") < stamp_loop.index("textContent = ")


def test_the_rewrite_is_guarded_and_uses_the_parts_api():
    assert "Intl.DateTimeFormat.prototype.formatToParts" in FOLLOW
    assert "formatToParts(when)" in FOLLOW


def test_since_last_look_compares_instants_padded_to_one_precision():
    """knot writes microseconds and the browser milliseconds; as strings, Z sorts above a digit,
    and a parsed Date holds only milliseconds, so both sides are padded to six digits."""
    block = FOLLOW[FOLLOW.index("knotview.lastLook") : FOLLOW.index("// Instants in the reader")]
    assert '"000000").slice(0, 6)' in block and "updatedAt > lastAt" in block
    assert "updated > last" not in block and "Date.parse" not in block
