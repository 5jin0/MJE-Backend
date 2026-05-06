import asyncio
from typing import List

from app.domains.recommendation.domain.service.image_relevance_service import ImageRelevanceService
from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    GetRecommendationResponseDto,
    RecommendationCourseItemDto,
    RecommendationPlaceDto,
)
from app.domains.recommendation.service.image_search_client_interface import (
    ImageSearchClientInterface,
)


class EnrichCourseImagesUseCase:
    def __init__(self, image_search_client: ImageSearchClientInterface) -> None:
        self._client = image_search_client
        self._relevance_service = ImageRelevanceService()

    async def execute(self, dto: GetRecommendationResponseDto, area: str) -> GetRecommendationResponseDto:
        loop = asyncio.get_running_loop()

        futures = [
            loop.run_in_executor(None, self._enrich_place, place, area)
            for course in dto.courses
            for place in course.places
        ]
        if futures:
            done, pending = await asyncio.wait(futures, timeout=0.8)
            for task in pending:
                task.cancel()

        for course in dto.courses:
            course.image_url = self._select_representative(course, area)

        return dto

    def _enrich_place(self, place: RecommendationPlaceDto, area: str) -> None:
        try:
            query = f"{area} {place.name}"
            images = self._client.search(query)
            for img in images:
                if self._relevance_service.validate_image(
                    img.title, img.link, place.name, area, place.category, place.keyword
                ):
                    place.image_url = img.link
                    return
        except Exception:
            pass
        place.image_url = None

    def _select_representative(self, course: RecommendationCourseItemDto, area: str) -> str | None:
        candidates = [
            (p.image_url, p.name, p.category, p.keyword)
            for p in course.places
        ]
        course_keywords = [area] + [
            keyword
            for p in course.places
            for keyword in [p.name, p.category, p.keyword]
        ]
        return self._relevance_service.select_representative_image(candidates, course_keywords) or None
