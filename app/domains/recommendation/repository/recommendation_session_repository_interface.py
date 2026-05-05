from abc import ABC, abstractmethod
from typing import Optional

from app.domains.recommendation.service.dto.recommendation_session_dto import RecommendationSessionDto


class RecommendationSessionRepositoryInterface(ABC):
    @abstractmethod
    async def save(self, session: RecommendationSessionDto) -> None: ...

    @abstractmethod
    async def find_by_course_id(self, course_id: str) -> Optional[RecommendationSessionDto]: ...
