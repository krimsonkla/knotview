"""The panel's surface: which paths exist, that every one is a GET, and what they answer with."""

import pytest
from fastapi.routing import APIRoute

from knotview.panel.app import panel
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
