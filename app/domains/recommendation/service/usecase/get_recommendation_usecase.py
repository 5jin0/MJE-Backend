import asyncio
import math
import uuid
from typing import List, Optional, Tuple

from app.domains.courses.domain.entity.course_entity import CourseEntity, CoursePlace
from app.domains.courses.domain.value_object.recommendation_place import RecommendationPlace
from app.domains.courses.repository.course_repository_interface import CourseRepositoryInterface
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
    RecommendationCourseItemDto,
)
from app.domains.recommendation.service.geocoding_client_interface import GeocodingClientInterface
from app.domains.recommendation.service.mapper.recommendation_response_mapper import (
    RecommendationResponseMapper,
)
from app.domains.recommendation.service.place_candidate_collector import PlaceCandidateCollector, filter_collection
from app.domains.recommendation.service.search_client_interface import SearchClientInterface


def _haversine_minutes(lat1: float, lon1: float, lat2: float, lon2: float, speed_mps: float) -> int:
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    dist = R * 2 * math.asin(math.sqrt(a))
    return max(1, round(dist / speed_mps / 60))


def _to_course_entity(course_item: RecommendationCourseItemDto, area: str, start_time: str, transport_str: str, session_id: str = "") -> CourseEntity:
    transport = Transport(transport_str)
    places_dto = course_item.places

    course_places: List[CoursePlace] = []
    for i, p in enumerate(places_dto):
        move_time = 0
        if i < len(places_dto) - 1:
            nxt = places_dto[i + 1]
            move_time = _haversine_minutes(p.latitude, p.longitude, nxt.latitude, nxt.longitude, transport.speed_mps)
        course_places.append(CoursePlace(
            order=p.order,
            place_type=p.place_type,
            id=0,
            name=p.name,
            category=p.category,
            road_address=p.road_address,
            address=p.address,
            mapx=str(p.longitude),
            mapy=str(p.latitude),
            link=p.link,
            telephone=p.telephone,
            keyword="",
            collected_at="",
            start_time=p.start_time,
            end_time=p.end_time,
            duration_minutes=p.duration_minutes,
            move_time_to_next_minutes=move_time,
        ))

    def _find_place(place_type: str) -> RecommendationPlace:
        p = next((p for p in places_dto if p.place_type == place_type), None)
        if p is None:
            return RecommendationPlace(id=0, name="", category="", road_address="", address="", mapx="", mapy="", link="", telephone="", keyword="", collected_at="")
        return RecommendationPlace(id=0, name=p.name, category=p.category, road_address=p.road_address, address=p.address, mapx=str(p.longitude), mapy=str(p.latitude), link=p.link, telephone=p.telephone, keyword="", collected_at="")

    total_duration = sum(cp.duration_minutes + cp.move_time_to_next_minutes for cp in course_places)
    place_names = ", ".join(p.name for p in places_dto)

    return CourseEntity(
        course_id=course_item.course_id,
        session_id=session_id,
        grade=course_item.grade,
        area=area,
        start_time=start_time,
        transport=transport_str,
        title=f"{area}에서 즐기는 데이트 코스",
        description=f"{area}에서 {place_names}을(를) 즐기는 하루 코스입니다.",
        estimated_duration_minutes=total_duration,
        restaurant=_find_place("restaurant"),
        cafe=_find_place("cafe"),
        activity=_find_place("activity"),
        places=course_places,
    )


class GetRecommendationUseCase:
    def __init__(
        self,
        session_repository: RecommendationSessionRepositoryInterface,
        search_client: SearchClientInterface,
        candidate_cache: Optional[CandidateCacheInterface] = None,
        geocoding_client: Optional[GeocodingClientInterface] = None,
        course_repository: Optional[CourseRepositoryInterface] = None,
    ) -> None:
        self._session_repository = session_repository
        self._collector = PlaceCandidateCollector(search_client)
        self._candidate_generator = CourseCandidateGeneratorService()
        self._selector = CourseSelectorService()
        self._mapper = RecommendationResponseMapper()
        self._candidate_cache = candidate_cache
        self._geocoding_client = geocoding_client
        self._course_repository = course_repository

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

        collection = filter_collection(collection)

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
            if self._course_repository:
                try:
                    session_id = str(uuid.uuid4())
                    for course_item in response.courses:
                        entity = _to_course_entity(course_item, dto.area, dto.start_time, dto.transport, session_id)
                        await self._course_repository.save(entity)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error("[MySQL] course save failed: %r", str(e))

        return response
