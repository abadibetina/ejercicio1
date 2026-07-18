from unittest.mock import MagicMock, patch

import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


def test_hello(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello DevOps"}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_db_check_ok(client):
    fake_conn = MagicMock()
    fake_conn.cursor.return_value.fetchone.return_value = (1,)

    with patch.object(app_module, "get_db_connection", return_value=fake_conn):
        response = client.get("/db-check")

    assert response.status_code == 200
    assert response.get_json() == {"database": "ok"}


def test_db_check_error(client):
    with patch.object(
        app_module, "get_db_connection", side_effect=Exception("connection refused")
    ):
        response = client.get("/db-check")

    assert response.status_code == 503
    body = response.get_json()
    assert body["database"] == "error"
    assert "connection refused" in body["detail"]


def test_cache_check_ok(client):
    fake_client = MagicMock()
    fake_client.ping.return_value = True

    with patch.object(app_module, "get_redis_connection", return_value=fake_client):
        response = client.get("/cache-check")

    assert response.status_code == 200
    assert response.get_json() == {"cache": "ok"}


def test_cache_check_error(client):
    with patch.object(
        app_module, "get_redis_connection", side_effect=Exception("cache unreachable")
    ):
        response = client.get("/cache-check")

    assert response.status_code == 503
    body = response.get_json()
    assert body["cache"] == "error"
    assert "cache unreachable" in body["detail"]
