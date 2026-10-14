from fastapi import APIRouter, Query, Request

from app.core.config import settings

router = APIRouter(prefix="/api/v1/pois", tags=["POIs"])


@router.get("/nearby")
async def get_nearby_pois(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    lang: str = Query(default="vi", pattern="^(vi|en|zh|ja|ko)$"),
):
    """Find published POIs near the visitor's location."""
    db = request.app.state.mongo_db

    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [lng, lat],
                },
                "key": "location",
                "distanceField": "distance_m",
                "maxDistance": settings.NEARBY_RADIUS_M,
                "spherical": True,
                "query": {
                    "status": "published",
                    "is_visible": True,
                },
            }
        }
    ]

    cursor = db["pois"].aggregate(pipeline)
    documents = await cursor.to_list(length=None)

    items = []
    for poi in documents:
        description = (
            poi.get(f"description_{lang}")
            or poi.get("description_en")
            or poi.get("description_vi")
            or ""
        )

        items.append(
            {
                "name": poi.get("name"),
                "address": poi.get("address"),
                "description": description,
                "image": poi.get("image"),
                "distance_m": round(poi["distance_m"], 2),
            }
        )

    return {"items": items}
