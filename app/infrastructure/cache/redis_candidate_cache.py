import json
from typing import Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.domains.recommendation.domain.value_object.activity_type import ActivityKind
from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.service.candidate_cache_interface import CandidateCacheInterface
from app.domains.recommendation.service.place_candidate_collector import PlaceCandidateCollection

_TTL_SECONDS = 60 * 30  # 30분


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
    return json.dumps({
        "restaurants": [_place_to_dict(p) for p in collection.restaurants],
        "cafes": [_place_to_dict(p) for p in collection.cafes],
        "activities": [_place_to_dict(p) for p in collection.activities],
        "shortage_reasons": collection.shortage_reasons,
    }, ensure_ascii=False)


def _deserialize(raw: str) -> PlaceCandidateCollection:
    data = json.loads(raw)
    return PlaceCandidateCollection(
        restaurants=[_dict_to_place(p) for p in data["restaurants"]],
        cafes=[_dict_to_place(p) for p in data["cafes"]],
        activities=[_dict_to_place(p) for p in data["activities"]],
        shortage_reasons=data["shortage_reasons"],
    )


def _place_to_dict(p: CandidatePlace) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "road_address": p.road_address,
        "address": p.address,
        "mapx": p.mapx,
        "mapy": p.mapy,
        "link": p.link,
        "telephone": p.telephone,
        "keyword": p.keyword,
        "collected_at": p.collected_at,
        "place_type": p.place_type.value,
        "activity_kind": p.activity_kind.value if p.activity_kind else None,
    }


def _dict_to_place(d: dict) -> CandidatePlace:
    return CandidatePlace(
        id=d["id"],
        name=d["name"],
        category=d["category"],
        road_address=d["road_address"],
        address=d["address"],
        mapx=d["mapx"],
        mapy=d["mapy"],
        link=d["link"],
        telephone=d["telephone"],
        keyword=d["keyword"],
        collected_at=d["collected_at"],
        place_type=PlaceType(d["place_type"]),
        activity_kind=ActivityKind(d["activity_kind"]) if d.get("activity_kind") else None,
    )
