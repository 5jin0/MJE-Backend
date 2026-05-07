import json
from datetime import time
from typing import List, Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.domains.recommendation.domain.value_object.place import Place
from app.domains.recommendation.service.candidate_cache_interface import CandidateCacheInterface
from app.domains.recommendation.service.place_candidate_collector import PlaceCandidateCollection

_TTL_SECONDS = 60 * 120  # 2시간


class RedisCandidateCache(CandidateCacheInterface):
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def get(self, area: str) -> Optional[PlaceCandidateCollection]:
        try:
            raw = await self._redis.get(self._key(area))
            if raw is None:
                return None
            return _deserialize(raw)
        except (RedisError, Exception):
            return None

    async def set(self, area: str, collection: PlaceCandidateCollection) -> None:
        try:
            await self._redis.setex(self._key(area), _TTL_SECONDS, _serialize(collection))
        except (RedisError, Exception):
            pass

    def _key(self, area: str) -> str:
        return f"candidate:area:{area}"


def _serialize(collection: PlaceCandidateCollection) -> str:
    return json.dumps(
        {
            "restaurants": [_place_to_dict(p) for p in collection.restaurants],
            "cafes": [_place_to_dict(p) for p in collection.cafes],
            "activities": [_place_to_dict(p) for p in collection.activities],
            "shortage_reasons": collection.shortage_reasons,
        },
        ensure_ascii=False,
    )


def _deserialize(raw: str) -> PlaceCandidateCollection:
    data = json.loads(raw)
    return PlaceCandidateCollection(
        restaurants=[_dict_to_place(p) for p in data["restaurants"]],
        cafes=[_dict_to_place(p) for p in data["cafes"]],
        activities=[_dict_to_place(p) for p in data["activities"]],
        shortage_reasons=data.get("shortage_reasons", []),
    )


def _place_to_dict(p: Place) -> dict:
    return {
        "name": p.name,
        "area": p.area,
        "category": p.category,
        "address": p.address,
        "road_address": p.road_address,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "search_rank": p.search_rank,
        "keywords": p.keywords,
        "activity_type": p.activity_type,
        "category_confidence": p.category_confidence,
        "image_url": p.image_url,
        "rating": p.rating,
        "has_parking": p.has_parking,
        "business_close_time": (
            p.business_close_time.strftime("%H:%M")
            if p.business_close_time is not None
            else None
        ),
        "score": p.score,
        "is_franchise": p.is_franchise,
        "place_key": p.place_key,
        "main_description": p.main_description,
        "brief_description": p.brief_description,
        "link": p.link,
        "telephone": p.telephone,
    }


def _dict_to_place(d: dict) -> Place:
    close_raw = d.get("business_close_time")
    business_close_time: Optional[time] = None
    if close_raw:
        try:
            h, m = map(int, close_raw.split(":"))
            business_close_time = time(h, m)
        except (ValueError, AttributeError):
            pass

    return Place(
        name=d["name"],
        area=d.get("area", ""),
        category=d["category"],
        address=d.get("address", ""),
        road_address=d.get("road_address", ""),
        latitude=d.get("latitude", 0.0),
        longitude=d.get("longitude", 0.0),
        search_rank=d.get("search_rank", 0),
        keywords=d.get("keywords", []),
        activity_type=d.get("activity_type"),
        category_confidence=d.get("category_confidence", 1.0),
        image_url=d.get("image_url"),
        rating=d.get("rating", 0.0),
        has_parking=d.get("has_parking", False),
        business_close_time=business_close_time,
        score=d.get("score", 0.0),
        is_franchise=d.get("is_franchise", False),
        place_key=d.get("place_key", ""),
        main_description=d.get("main_description", ""),
        brief_description=d.get("brief_description", ""),
        link=d.get("link", ""),
        telephone=d.get("telephone", ""),
    )
