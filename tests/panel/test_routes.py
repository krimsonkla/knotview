"""The panel's surface: which paths exist, that every one is a GET, and what they answer with."""

import pytest
from fastapi.routing import APIRoute

from knotview.panel.app import HERE, _asset_stamp, panel
from tests.panel.declared import DeclaredBacklog

PATHS = {
    "/static",
    "/",
    "/tickets",
    "/tree",
    "/queue/{which}",
    "/ticket/{identifier}",
    "/digest",
    "/live",
    "/tags",
}


def test_the_route_table_is_exactly_these_paths():
    assert {route.path for route in panel(DeclaredBacklog()).routes} == PATHS


def test_every_route_is_a_get():
    """The read-only guarantee at the HTTP surface. /static is a Mount with no methods and is
    covered by the path assertion above."""
    routes = [route for route in panel(DeclaredBacklog()).routes if isinstance(route, APIRoute)]

    assert len(routes) == 8
    assert all(route.methods == {"GET"} for route in routes)


@pytest.mark.parametrize(
    "path", ["/", "/tickets", "/tree", "/queue/ready", "/ticket/pro-01m2aaaaaaaa"]
)
def test_pages_answer_as_html(client, path):
    assert client(DeclaredBacklog()).get(path).headers["content-type"].startswith("text/html")


def test_the_digest_answers_as_text(client):
    response = client(DeclaredBacklog()).get("/digest")

    assert response.headers["content-type"].startswith("text/plain")


def test_a_request_addressed_to_another_host_is_refused(client):
    """DNS rebinding: a page elsewhere can point a browser at this loopback port under its own
    name, and the backlog must not answer it."""
    response = client(DeclaredBacklog()).get("/", headers={"host": "evil.example"})

    assert response.status_code == 400
    assert "The parent" not in response.text


def test_localhost_is_an_accepted_name(client):
    assert client(DeclaredBacklog()).get("/", headers={"host": "localhost:7778"}).status_code == 200


def test_static_urls_carry_a_stamp_that_moves_with_the_files(client, tmp_path):
    """A browser keeps a static file by heuristic; a new version must be a new URL. The stamp
    must move when a file's content changes under the same name, which is the case that bit, and
    when a file appears in a subdirectory, which the first glob missed."""
    page = client(DeclaredBacklog()).get("/tickets").text
    stamp = page.split('href="/static/panel.css?v=')[1].split('"')[0]
    (tmp_path / "a.js").write_text("one")
    first = _asset_stamp(tmp_path)
    (tmp_path / "a.js").write_text("two")
    edited = _asset_stamp(tmp_path)
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b").write_text("three")
    nested = _asset_stamp(tmp_path)

    assert stamp == _asset_stamp(HERE / "static") and f'src="/static/follow.js?v={stamp}"' in page
    assert len({first, edited, nested}) == 3
