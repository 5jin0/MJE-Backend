from typing import Dict, Optional

from app.domains.recommendation.repository.recommendation_session_repository_interface import (
    RecommendationSessionRepositoryInterface,
)
from app.domains.recommendation.service.dto.recommendation_session_dto import RecommendationSessionDto

_store: Dict[str, RecommendationSessionDto] = {}


class InMemoryRecommendationSessionRepository(RecommendationSessionRepositoryInterface):
    def save(self, session: RecommendationSessionDto) -> None:
        for course in session.courses:
            _store[course.course_id] = session

    def find_by_course_id(self, course_id: str) -> Optional[RecommendationSessionDto]:
        return _store.get(course_id)


_instance = InMemoryRecommendationSessionRepository()


def get_recommendation_session_repository() -> InMemoryRecommendationSessionRepository:
    return _instance
