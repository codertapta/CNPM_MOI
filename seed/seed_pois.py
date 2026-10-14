import json
import os
from pathlib import Path

from pymongo import MongoClient

ROOT = Path(__file__).resolve().parent
SEED_FILE = ROOT / "pois.json"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "automatic_dubbing")


def main():
    with SEED_FILE.open("r", encoding="utf-8-sig") as file:
        pois = json.load(file)

    if not isinstance(pois, list):
        raise ValueError("seed/pois.json must contain a JSON list")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

    try:
        db = client[MONGO_DB_NAME]
        collection = db["pois"]

        collection.create_index(
            [("location", "2dsphere")],
            name="pois_location_2dsphere",
        )

        for poi in pois:
            name = poi["name"].strip()
            lat = float(poi["lat"])
            lng = float(poi["lng"])

            if not name or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise ValueError(f"Invalid POI data: {name!r}")

            document = {
                "name": name,
                "address": poi.get("address"),
                "location": {
                    "type": "Point",
                    "coordinates": [lng, lat],
                },
                "description_vi": poi["description_vi"],
                "image": poi.get("image"),
                "status": "published",
                "is_visible": True,
            }

            collection.update_one(
                {"name": name},
                {"$set": document},
                upsert=True,
            )

        print(f"Seed input: {len(pois)} POIs")
        print(f"POIs in database: {collection.count_documents({})}")
        print("Geo index:", collection.index_information()["pois_location_2dsphere"])

    finally:
        client.close()


if __name__ == "__main__":
    main()
