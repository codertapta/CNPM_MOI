import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app, frontend_fallback, health, health_ready


def test_health_returns_ok_and_version():
    response = asyncio.run(health())

    assert response == {
        "status": "ok",
        "version": settings.GIT_SHA,
    }


@pytest.mark.anyio
async def test_health_ready_success():
    mock_db = MagicMock()
    mock_db.command = AsyncMock(return_value={"ok": 1})
    mock_db.__getitem__.return_value = MagicMock()

    mock_gridfs = MagicMock()
    mock_gridfs.upload_from_stream = AsyncMock(return_value="test-file-id")
    mock_stream = MagicMock()
    mock_stream.read = AsyncMock(return_value=b"gridfs-health-check")
    mock_gridfs.open_download_stream = AsyncMock(return_value=mock_stream)
    mock_gridfs.delete = AsyncMock()

    test_app = FastAPI()
    test_app.state.mongo_db = mock_db
    test_app.state.gridfs = mock_gridfs
    test_app.get("/health/ready")(health_ready)

    with patch("app.main.settings", settings):
        with TestClient(test_app) as client:
            response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
        "gridfs": "ok",
        "version": settings.GIT_SHA,
    }
    mock_db.command.assert_awaited_once_with("ping")
    mock_gridfs.delete.assert_awaited_once_with("test-file-id")


@pytest.mark.anyio
async def test_health_ready_returns_503_when_database_fails():
    mock_db = MagicMock()
    mock_db.command = AsyncMock(side_effect=RuntimeError("database unavailable"))

    mock_gridfs = MagicMock()

    test_app = FastAPI()
    test_app.state.mongo_db = mock_db
    test_app.state.gridfs = mock_gridfs
    test_app.get("/health/ready")(health_ready)

    with TestClient(test_app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert "Service not ready" in response.json()["detail"]


def test_frontend_fallback_returns_404_for_api_paths():
    test_app = FastAPI()
    test_app.get("/{full_path:path}")(frontend_fallback)

    with TestClient(test_app) as client:
        response = client.get("/api/unknown")

    assert response.status_code == 404


def test_frontend_fallback_returns_404_when_build_missing():
    test_app = FastAPI()
    test_app.get("/{full_path:path}")(frontend_fallback)

    with (
        patch("app.main.FRONTEND_DIST") as mock_dist,
        TestClient(test_app) as client,
    ):
        mock_dist.__truediv__.return_value.is_file.return_value = False
        response = client.get("/unknown-page")

    assert response.status_code == 404
    assert response.json()["detail"] == "Frontend build not found"


def test_app_registers_expected_routes():
    from fastapi.routing import APIRoute

    # Các route trực tiếp được đăng ký trong ứng dụng.
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}

    assert "/health" in paths
    assert "/health/ready" in paths

    # Kiểm tra endpoint POI thông qua OpenAPI,
    # nơi FastAPI tổng hợp các route đã đăng ký.
    schema = app.openapi()
    assert "/api/v1/pois/nearby" in schema["paths"]
