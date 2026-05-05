import asyncio
from typing import Optional

from app.domains.recommendation.domain.service.course_candidate_generator_service import (
    CourseCandidateGeneratorService,
)
from app.domains.recommendation.domain.service.course_ordering_service import CourseOrderingService
from app.domains.recommendation.domain.service.course_selector_service import CourseSelectorService
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot
from app.domains.recommendation.domain.value_object.transport import Transport
from app.domains.recommendation.repository.recommendation_session_repository_interface import (
    RecommendationSessionRepositoryInterface,
)
from app.domains.recommendation.service.candidate_cache_interface import CandidateCacheInterface
from app.domains.recommendation.service.dto.recommendation_session_dto import RecommendationSessionDto
from app.domains.recommendation.service.dto.request.get_recommendation_request_dto import (
    GetRecommendationRequestDto,
)
from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    GetRecommendationResponseDto,
)
from app.domains.recommendation.service.image_search_client_interface import (
    ImageSearchClientInterface,
)
from app.domains.recommendation.service.mapper.recommendation_response_mapper import (
    RecommendationResponseMapper,
)
from app.domains.recommendation.service.place_candidate_collector import PlaceCandidateCollector
from app.domains.recommendation.service.search_client_interface import SearchClientInterface
from app.domains.recommendation.service.usecase.enrich_course_images_usecase import (
    EnrichCourseImagesUseCase,
)


class GetRecommendationUseCase:
    def __init__(
        self,
        session_repository: RecommendationSessionRepositoryInterface,
        search_client: SearchClientInterface,
        image_search_client: ImageSearchClientInterface,
        candidate_cache: Optional[CandidateCacheInterface] = None,
    ) -> None:
        self._session_repository = session_repository
        self._collector = PlaceCandidateCollector(search_client)
        self._candidate_generator = CourseCandidateGeneratorService()
        self._ordering_service = CourseOrderingService()
        self._selector = CourseSelectorService()
        self._mapper = RecommendationResponseMapper()
        self._image_enricher = EnrichCourseImagesUseCase(image_search_client)
        self._candidate_cache = candidate_cache

    async def execute(self, dto: GetRecommendationRequestDto) -> GetRecommendationResponseDto:
        collection = None
        if self._candidate_cache:
            collection = await self._candidate_cache.get(dto.area)

        if collection is None:
            collection = await self._collector.collect(dto.area)
            if self._candidate_cache:
                asyncio.create_task(self._candidate_cache.set(dto.area, collection))
        candidates, candidate_shortages = self._candidate_generator.generate(
            collection.restaurants,
            collection.cafes,
            collection.activities,
        )

        transport = Transport(dto.transport)
        ordered_results = [
            self._ordering_service.apply_order(candidate, dto.start_time, transport)
            for candidate in candidates
        ]
        valid_results = [result for result in ordered_results if result.is_valid]

        best, optionals = self._selector.select(
            valid_results,
            TimeSlot.from_start_time(dto.start_time),
            transport,
        )

        shortage_reasons = [
            *collection.shortage_reasons,
            *candidate_shortages,
        ]
        if not valid_results:
            shortage_reasons.append("조건에 맞는 추천 코스를 만들지 못했어요. 다른 지역이나 시간대로 다시 시도해 보세요.")

        response = self._mapper.to_response_dto(best, optionals, shortage_reasons)
        response = await self._image_enricher.execute(response, dto.area)

        if response.courses:
            asyncio.create_task(
                self._session_repository.save(
                    RecommendationSessionDto(
                        area=dto.area,
                        start_time=dto.start_time,
                        transport=dto.transport,
                        courses=response.courses,
                    )
                )
            )

        return response
