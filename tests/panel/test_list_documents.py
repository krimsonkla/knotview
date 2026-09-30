"""Documents in the ticket lists: the column, the filter, its chips and its links."""

from dataclasses import replace
from urllib.parse import parse_qs

from knotview.panel.selection import Selection
from knotview.values.attention import Attention
from tests.panel.declared import CHILD, CLOSED, ORPHAN, PARENT, PROJECT, DeclaredBacklog, ticket

# A project requiring a spec and a plan before a ticket enters in_progress. The parent owns both,
# the in-progress child and the open orphan own nothing, so both lack them.
REQUIRING = replace(PROJECT, required_docs=(("in_progress", ("spec", "plan")),))


def asked(query: str, project=REQUIRING) -> Selection:
    """The selection a query string asks for, read the way the pages read it."""
    given = parse_qs(query)
    return Selection.asked(
        project, {name: values[-1] for name, values in given.items()}, docs=given.get("doc", [])
    )


def test_ticked_types_are_kept_in_declared_order_and_an_undeclared_one_is_dropped():
    assert asked("doc=plan&doc=memo&doc=spec").docs == ("spec", "plan")


def test_none_attached_clears_the_ticked_types():
    chosen = asked("doc=spec&nodocs=1")

    assert chosen.undocumented and not chosen.docs


def test_a_ticket_matches_when_it_owns_every_ticked_type():
    both = asked("doc=spec&doc=plan")
    spec_only = replace(PARENT, documents=PARENT.documents[1:])

    assert both.matches(PARENT, REQUIRING)
    assert not both.matches(spec_only, REQUIRING)
    assert not both.matches(ORPHAN, REQUIRING)


def test_none_attached_matches_only_tickets_owning_nothing():
    chosen = asked("nodocs=1")

    assert chosen.matches(ORPHAN, REQUIRING) and not chosen.matches(PARENT, REQUIRING)


def test_lacking_matches_live_tickets_missing_a_required_type_and_never_a_closed_one():
    chosen = asked("lacking=1")

    assert chosen.matches(CHILD, REQUIRING) and chosen.matches(ORPHAN, REQUIRING)
    assert not chosen.matches(PARENT, REQUIRING)
    assert not chosen.matches(CLOSED, REQUIRING)


def test_each_chip_drops_only_itself():
    chosen = asked("type=task&doc=spec&doc=plan&lacking=1")
    chips = {label: query for label, _, query in chosen.chips()}

    assert parse_qs(chips["has spec"]) == {"type": ["task"], "doc": ["plan"], "lacking": ["1"]}
    assert parse_qs(chips["has plan"]) == {"type": ["task"], "doc": ["spec"], "lacking": ["1"]}
    assert parse_qs(chips["missing a required type"]) == {"type": ["task"], "doc": ["spec", "plan"]}
    assert chosen.without("has spec") == chips["has spec"]
    assert parse_qs(asked(chips["has spec"]).without("has plan")) == {
        "type": ["task"],
        "lacking": ["1"],
    }


def test_none_attached_is_a_chip_of_its_own():
    chips = [label for label, _, _ in asked("nodocs=1").chips()]

    assert chips == ["none attached"]
    assert asked("nodocs=1").filtering


def test_links_are_percent_encoded_and_read_back_to_the_same_values():
    odd = replace(REQUIRING, doc_types=("a b&c",))
    chosen = replace(asked("", odd), tag="x y&z", docs=("a b&c",))

    built = chosen.query_string()

    assert "tag=x%20y%26z" in built and "doc=a%20b%26c" in built
    assert parse_qs(built) == {"tag": ["x y&z"], "doc": ["a b&c"]}


def page(client, path: str, **backlog) -> str:
    """One rendered page over a declared backlog whose project requires documents."""
    return client(DeclaredBacklog(project_value=REQUIRING, **backlog)).get(path).text


def test_a_row_shows_its_types_in_declared_order_linking_to_its_documents(client):
    text = page(client, "/tickets")

    row = text[text.index("The parent") :]
    row = row[: row.index("</tr>")]
    assert row.index(">spec<") < row.index(">plan<")
    assert 'href="/ticket/pro-01m2aaaaaaaa#documents"' in row


def test_missing_types_are_dashed_on_the_list_and_the_ready_queue(client):
    listed = page(client, "/tickets")
    queued = page(client, "/queue/ready")

    assert 'class="doctype missing" title="needed to enter in_progress"' in listed
    assert 'class="doctype missing"' in queued


def test_no_dashed_type_on_the_overview_even_where_a_card_shows_a_lacking_ticket(client):
    stale = Attention(in_progress=(), ready_to_close=(), stale=(ORPHAN,))

    text = page(client, "/", attention_value=stale)

    assert "The orphan" in text and 'class="doctype missing"' not in text


def test_the_tree_lists_show_dashed_types_as_its_rows_do(client):
    # Story 3 kept dashes off the tree; kno-01m3q9rs9632 turned them on, rows and lists alike.
    text = page(client, "/tree")

    assert "The orphan" in text and 'class="doctype missing"' in text


def test_the_empty_row_spans_every_column_when_the_docs_column_shows(client):
    bare = (ticket("pro-01m2eeeeeeee", title="Bare"),)

    text = client(DeclaredBacklog(live_value=bare)).get("/tickets?doc=spec").text

    assert text.count("</th>") == 11 and 'colspan="11"' in text


def test_the_column_hides_without_any_types_and_shows_when_a_documents_filter_is_on(client):
    bare = (ticket("pro-01m2eeeeeeee", title="Bare"),)
    plain = client(DeclaredBacklog(live_value=bare)).get("/tickets").text
    filtered = client(DeclaredBacklog(live_value=bare)).get("/tickets?nodocs=1").text

    assert "<th>docs</th>" not in plain
    assert "<th>docs</th>" in filtered and "Bare" in filtered


def test_the_filter_keeps_tickets_owning_every_ticked_type(client):
    text = page(client, "/tickets?doc=spec&doc=plan")

    assert "The parent" in text and "The orphan" not in text and "The child" not in text


def test_an_undeclared_type_is_ignored_rather_than_emptying_the_list(client):
    text = page(client, "/tickets?doc=memo")

    assert "The parent" in text and "The orphan" in text and "has memo" not in text


def test_none_attached_shows_only_tickets_owning_nothing_and_drops_ticked_types(client):
    text = page(client, "/tickets?nodocs=1&doc=spec")

    assert "The orphan" in text and "The parent" not in text
    assert "none attached" in text and "has spec" not in text


def test_lacking_shows_live_tickets_missing_a_type_each_with_its_dashes(client):
    text = page(client, "/tickets?lacking=1&closed=1")

    assert "The orphan" in text and "The child" in text
    assert "The parent" not in text and "The closed one" not in text


def test_each_type_chip_links_to_the_list_without_only_that_type(client):
    text = page(client, "/tickets?doc=spec&doc=plan")

    assert 'href="/tickets?doc=plan" title="drop this filter"' in text
    assert 'href="/tickets?doc=spec" title="drop this filter"' in text


def test_the_filter_offers_each_declared_type_as_a_checkbox_ticked_as_asked(client):
    text = page(client, "/tickets?doc=plan")

    assert 'name="doc" value="plan" checked' in text
    assert 'name="doc" value="spec" />' in text
    assert 'name="nodocs" value="1"' in text and 'name="lacking" value="1"' in text


def test_lacking_is_neither_offered_nor_applied_where_the_project_requires_nothing(client):
    text = client(DeclaredBacklog()).get("/tickets?lacking=1").text

    assert 'name="lacking"' not in text and "missing a required type" not in text
    assert "The orphan" in text and "The parent" in text


def test_hand_built_links_encode_a_tag_and_an_assignee(client):
    # A second assignee, or the list says it once and draws no assignee link.
    odd = (
        ticket("pro-01m2eeeeeeee", title="Odd", tags=("r&d",), assignee="a b"),
        ticket("pro-01m2ffffffff", title="Other"),
    )

    listed = client(DeclaredBacklog(live_value=odd)).get("/tickets").text
    shown = client(DeclaredBacklog(live_value=odd)).get("/ticket/pro-01m2eeeeeeee").text

    for text in (listed, shown):
        assert 'href="/tickets?tag=r%26d"' in text and 'href="/tickets?assignee=a%20b"' in text


def test_a_dashed_tag_names_every_status_that_needs_its_type(client):
    gated = replace(
        REQUIRING, required_docs=(("open", ("spec",)), ("in_progress", ("spec", "plan")))
    )

    text = client(DeclaredBacklog(project_value=gated)).get("/tickets").text

    assert 'class="doctype missing" title="needed to enter open, in_progress">spec<' in text
