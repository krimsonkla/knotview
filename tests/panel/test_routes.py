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
}


def test_the_route_table_is_exactly_these_paths():
    assert {route.path for route in panel(DeclaredBacklog()).routes} == PATHS


def test_every_route_is_a_get():
    """The read-only guarantee at the HTTP surface. /static is a Mount with no methods and is
    covered by the path assertion above."""
    routes = [route for route in panel(DeclaredBacklog()).routes if isinstance(route, APIRoute)]

    assert len(routes) == 7
    assert all(route.methods == {"GET"} for route in routes)


@pytest.mark.parametrize(
    "path", ["/", "/tickets", "/tree", "/queue/ready", "/ticket/pro-01m2aaaaaaaa"]
)
def test_pages_answer_as_html(client, path):
    assert client(DeclaredBacklog()).get(path).headers["content-type"].startswith("text/html")


def test_the_digest_answers_as_text(client):
    response = client(DeclaredBacklog()).get("/digest")

    assert response.headers["content-type"].startswith("text/plain")
