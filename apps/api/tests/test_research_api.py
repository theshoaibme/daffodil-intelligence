"""Research library API tests."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_list_research_categories(client):
    res = client.get("/api/research/categories")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "form_categories" in data
    assert "Others" in data["form_categories"]


def test_list_public_papers(client):
    res = client.get("/api/research/papers")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["limit"] == 16


def test_get_public_paper_not_found(client):
    res = client.get("/api/research/papers/does-not-exist")
    assert res.status_code == 404
