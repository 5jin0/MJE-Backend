import asyncio
from typing import Optional, Tuple

from app.domains.recommendation.domain.service.course_candidate_generator_service import (
    CourseCandidateGeneratorService,
)
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
from app.domains.recommendation.service.geocoding_client_interface import GeocodingClientInterface
from app.domains.recommendation.service.mapper.recommendation_response_mapper import (
    RecommendationResponseMapper,
)
from app.domains.recommendation.service.place_candidate_collector import PlaceCandidateCollector
from app.domains.recommendation.service.search_client_interface import SearchClientInterface


class GetRecommendationUseCase:
    def __init__(
        self,
        session_repository: RecommendationSessionRepositoryInterface,
        search_client: SearchClientInterface,
        candidate_cache: Optional[CandidateCacheInterface] = None,
        geocoding_client: Optional[GeocodingClientInterface] = None,
    ) -> None:
        self._session_repository = session_repository
        self._collector = PlaceCandidateCollector(search_client)
        self._candidate_generator = CourseCandidateGeneratorService()
        self._selector = CourseSelectorService()
        self._mapper = RecommendationResponseMapper()
        self._candidate_cache = candidate_cache
        self._geocoding_client = geocoding_client

    async def _geocode(self, area: str) -> Optional[Tuple[float, float]]:
        if not self._geocoding_client:
            return None
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, self._geocoding_client.geocode, area)
        except Exception:
            return None

    async def _get_cached_collection(self, area: str):
        if not self._candidate_cache:
            return None
        return await self._candidate_cache.get(area)

    async def execute(self, dto: GetRecommendationRequestDto) -> GetRecommendationResponseDto:
        # Step 1: geocoding (background) + cache check
        geocode_task = asyncio.create_task(self._geocode(dto.area))
        collection = await self._get_cached_collection(dto.area)

        if collection is not None:
            geocode_task.cancel()
        else:
            center_coords = await geocode_task
            # Step 2-3: collect and cache candidates
            collection = await self._collector.collect(dto.area, center_coords)
            if self._candidate_cache:
                asyncio.create_task(self._candidate_cache.set(dto.area, collection))

        # Step 4: generate course candidates
        candidates, candidate_shortages = self._candidate_generator.generate(
            collection.restaurants,
            collection.cafes,
            collection.activities,
            dto.start_time,
            seed=dto.seed,
        )

        # Step 5: score and select courses
        transport = Transport(dto.transport)
        time_slot = TimeSlot.from_start_time(dto.start_time)

        best, optionals = self._selector.select(
            candidates,
            dto.start_time,
            transport,
            time_slot,
        )

        shortage_reasons = [
            *collection.shortage_reasons,
            *candidate_shortages,
        ]
        if best is None:
            shortage_reasons.append(
                "조건에 맞는 추천 코스를 만들지 못했어요. 다른 지역이나 시간대로 다시 시도해 보세요."
            )

        response = self._mapper.to_response_dto(best, optionals, shortage_reasons)

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
