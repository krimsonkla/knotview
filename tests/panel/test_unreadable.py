"""The page that admits the backlog could not be read."""

from tests.panel.declared import RefusingBacklog


def test_a_backlog_that_cannot_be_read_renders_the_refusal_and_its_advice_at_503(client):
    response = client(RefusingBacklog()).get("/")

    assert response.status_code == 503
    assert "no knot project here" in response.text
    assert "run knot init, or point elsewhere" in response.text
