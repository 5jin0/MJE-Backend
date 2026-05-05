import json
from dataclasses import asdict
from typing import Dict, Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.domains.recommendation.repository.recommendation_session_repository_interface import (
    RecommendationSessionRepositoryInterface,
)
from app.domains.recommendation.service.dto.recommendation_session_dto import RecommendationSessionDto
from app.infrastructure.cache.redis_client import get_redis

_SESSION_TTL_SECONDS = 60 * 60 * 6
_fallback_store: Dict[str, RecommendationSessionDto] = {}


class RedisRecommendationSessionRepository(RecommendationSessionRepositoryInterface):
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def save(self, session: RecommendationSessionDto) -> None:
        payload = json.dumps(asdict(session), ensure_ascii=False)

        try:
            for course in session.courses:
                await self._redis.setex(
                    self._build_key(course.course_id),
                    _SESSION_TTL_SECONDS,
                    payload,
                )
        except RedisError:
            for course in session.courses:
                _fallback_store[course.course_id] = session

    async def find_by_course_id(self, course_id: str) -> Optional[RecommendationSessionDto]:
        try:
            raw = await self._redis.get(self._build_key(course_id))
        except RedisError:
            return _fallback_store.get(course_id)

        if raw is None:
            return _fallback_store.get(course_id)

        data = json.loads(raw)
        return RecommendationSessionDto.from_dict(data)

    def _build_key(self, course_id: str) -> str:
        return f"recommendation:course:{course_id}"


async def get_recommendation_session_repository() -> RedisRecommendationSessionRepository:
    redis_client = await get_redis()
    return RedisRecommendationSessionRepository(redis_client)
