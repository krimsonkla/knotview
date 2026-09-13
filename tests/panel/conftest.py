"""A client over the panel, built per test so a backlog can be declared for it."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from knotview.panel.app import panel


@pytest.fixture
def client() -> Callable[..., TestClient]:
    """A builder for clients, since each test declares its own backlog."""

    def build(backlog, **options) -> TestClient:
        """A client over the panel built on that backlog, with any panel options passed through."""
        return TestClient(panel(backlog, **options))

    return build
