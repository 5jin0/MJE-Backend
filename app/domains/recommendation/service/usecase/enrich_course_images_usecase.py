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

_FALLBACK_IMAGES = {
    "restaurant": None,
    "cafe": None,
    "activity": None,
}


class EnrichCourseImagesUseCase:
    def __init__(self, image_search_client: ImageSearchClientInterface) -> None:
        self._client = image_search_client
        self._relevance_service = ImageRelevanceService()

    async def execute(self, dto: GetRecommendationResponseDto, area: str) -> GetRecommendationResponseDto:
        loop = asyncio.get_running_loop()

        # 모든 코스의 모든 장소 이미지를 동시에 검색
        place_tasks = [
            (course, place, label)
            for course in dto.courses
            for place, label in [
                (course.restaurant, "restaurant"),
                (course.cafe, "cafe"),
                (course.activity, "activity"),
            ]
        ]
        await asyncio.gather(*[
            loop.run_in_executor(None, self._enrich_place, place, label, area)
            for _, place, label in place_tasks
        ])

        for course in dto.courses:
            course.image_url = self._select_representative(course, area)

        return dto

    def _enrich_place(self, place: RecommendationPlaceDto, place_type_label: str, area: str) -> None:
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

        place.image_url = _FALLBACK_IMAGES.get(place_type_label)

    def _select_representative(self, course: RecommendationCourseItemDto, area: str) -> str | None:
        candidates = [
            (course.restaurant.image_url, course.restaurant.name, course.restaurant.category, course.restaurant.keyword),
            (course.cafe.image_url, course.cafe.name, course.cafe.category, course.cafe.keyword),
            (course.activity.image_url, course.activity.name, course.activity.category, course.activity.keyword),
        ]
        course_keywords = _build_course_keywords(course, area)
        return self._relevance_service.select_representative_image(candidates, course_keywords) or None


def _build_course_keywords(course: RecommendationCourseItemDto, area: str) -> List[str]:
    return [
        area,
        course.restaurant.name, course.restaurant.category, course.restaurant.keyword,
        course.cafe.name, course.cafe.category, course.cafe.keyword,
        course.activity.name, course.activity.category, course.activity.keyword,
    ]
