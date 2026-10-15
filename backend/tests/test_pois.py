from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.pois import router
from app.core.config import settings


@pytest.fixture
def client_and_db():
    test_app = FastAPI()
    test_app.include_router(router)

    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_db.__getitem__.return_value.aggregate.return_value = mock_cursor

    test_app.state.mongo_db = mock_db

    with TestClient(test_app) as client:
        yield client, mock_db, mock_cursor


def test_nearby_returns_empty_items(client_and_db):
    client, _, _ = client_and_db

    response = client.get("/api/v1/pois/nearby?lat=10.7769&lng=106.7009")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_nearby_uses_correct_geo_query(client_and_db):
    client, mock_db, _ = client_and_db

    response = client.get("/api/v1/pois/nearby?lat=10.7769&lng=106.7009")

    assert response.status_code == 200

    pipeline = mock_db["pois"].aggregate.call_args.args[0]
    geo_near = pipeline[0]["$geoNear"]

    assert geo_near["near"]["type"] == "Point"
    assert geo_near["near"]["coordinates"] == [106.7009, 10.7769]
    assert geo_near["key"] == "location"
    assert geo_near["distanceField"] == "distance_m"
    assert geo_near["maxDistance"] == settings.NEARBY_RADIUS_M
    assert geo_near["spherical"] is True
    assert geo_near["query"] == {
        "status": "published",
        "is_visible": True,
    }


@pytest.mark.parametrize(
    ("lang", "expected_description"),
    [
        ("vi", "Mô tả tiếng Việt"),
        ("en", "English description"),
        ("zh", "中文描述"),
        ("ja", "日本語の説明"),
        ("ko", "한국어 설명"),
    ],
)
def test_nearby_selects_requested_language(client_and_db, lang, expected_description):
    client, mock_db, mock_cursor = client_and_db

    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "name": "Test POI",
                "address": "Test address",
                "description_vi": "Mô tả tiếng Việt",
                "description_en": "English description",
                "description_zh": "中文描述",
                "description_ja": "日本語の説明",
                "description_ko": "한국어 설명",
                "image": "test.jpg",
                "distance_m": 123.456,
            }
        ]
    )

    response = client.get(f"/api/v1/pois/nearby?lat=10.7769&lng=106.7009&lang={lang}")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["description"] == expected_description
    assert item["distance_m"] == 123.46
    assert item["name"] == "Test POI"
    assert item["address"] == "Test address"
    assert item["image"] == "test.jpg"


@pytest.mark.parametrize(
    ("query",),
    [
        ("lat=91&lng=106",),
        ("lat=-91&lng=106",),
        ("lat=10&lng=181",),
        ("lat=10&lng=-181",),
        ("lat=10&lng=106&lang=fr",),
        ("lng=106",),
        ("lat=10",),
    ],
)
def test_nearby_rejects_invalid_query_parameters(client_and_db, query):
    client, _, _ = client_and_db

    response = client.get(f"/api/v1/pois/nearby?{query}")

    assert response.status_code == 400 or response.status_code == 422


def test_nearby_falls_back_to_english_description(client_and_db):
    client, _, mock_cursor = client_and_db
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "name": "Test POI",
                "distance_m": 10,
                "description_vi": "Mô tả tiếng Việt",
                "description_en": "English fallback",
            }
        ]
    )

    response = client.get("/api/v1/pois/nearby?lat=10&lng=106&lang=zh")

    assert response.status_code == 200
    assert response.json()["items"][0]["description"] == "English fallback"


def test_nearby_falls_back_to_vietnamese_description(client_and_db):
    client, _, mock_cursor = client_and_db
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "name": "Test POI",
                "distance_m": 10,
                "description_vi": "Mô tả tiếng Việt",
            }
        ]
    )

    response = client.get("/api/v1/pois/nearby?lat=10&lng=106&lang=ja")

    assert response.status_code == 200
    assert response.json()["items"][0]["description"] == "Mô tả tiếng Việt"


def test_nearby_uses_empty_description_when_all_missing(client_and_db):
    client, _, mock_cursor = client_and_db
    mock_cursor.to_list = AsyncMock(
        return_value=[
            {
                "name": "Test POI",
                "distance_m": 10,
            }
        ]
    )

    response = client.get("/api/v1/pois/nearby?lat=10&lng=106")

    assert response.status_code == 200
    assert response.json()["items"][0]["description"] == ""
