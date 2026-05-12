import asyncio
import math
from typing import Dict, List, Optional

from app.common.exceptions import NotFoundError
from app.domains.recommendation.domain.value_object.transport import Transport
from app.domains.recommendation.repository.recommendation_session_repository_interface import (
    RecommendationSessionRepositoryInterface,
)
from app.domains.recommendation.service.dto.request.get_course_detail_request_dto import (
    GetCourseDetailRequestDto,
)
from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    CourseDetailPlaceDto,
    GetCourseDetailResponseDto,
    OtherCourseDto,
)
from app.domains.recommendation.service.dto.recommendation_session_dto import RecommendationSessionDto
from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    RecommendationCourseItemDto,
    RecommendationPlaceDto,
)
from app.domains.recommendation.service.map_client_interface import MapClientInterface, RouteRequest

def _travel_minutes(lat1: float, lon1: float, lat2: float, lon2: float, speed_mps: float) -> int:
    R = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    distance_m = R * 2 * math.asin(math.sqrt(a))
    return max(1, round(distance_m / speed_mps / 60))


_SHORT_DESCRIPTIONS: Dict[str, str] = {
    "restaurant": "맛있는 식사로 데이트를 풍성하게 즐기세요.",
    "cafe": "분위기 좋은 카페에서 여유로운 시간을 보내세요.",
    "activity": "특별한 활동으로 잊지 못할 추억을 만들어보세요.",
}


def _add_minutes(time_str: str, minutes: int) -> str:
    h, m = map(int, time_str.split(":"))
    total = h * 60 + m + minutes
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


class GetCourseDetailUseCase:
    def __init__(
        self,
        repository: RecommendationSessionRepositoryInterface,
        map_client: Optional[MapClientInterface] = None,
    ) -> None:
        self._repository = repository
        self._map_client = map_client

    async def _get_move_minutes(
        self,
        from_place: RecommendationPlaceDto,
        to_place: RecommendationPlaceDto,
        transport: Transport,
    ) -> int:
        if transport == Transport.CAR and self._map_client:
            loop = asyncio.get_running_loop()
            route = await loop.run_in_executor(
                None,
                self._map_client.get_route,
                RouteRequest(
                    from_mapx=str(from_place.longitude),
                    from_mapy=str(from_place.latitude),
                    to_mapx=str(to_place.longitude),
                    to_mapy=str(to_place.latitude),
                    transport=transport,
                ),
            )
            return route.duration_minutes
        return _travel_minutes(
            from_place.latitude, from_place.longitude,
            to_place.latitude, to_place.longitude,
            transport.speed_mps,
        )

    async def execute(self, dto: GetCourseDetailRequestDto) -> GetCourseDetailResponseDto:
        if not dto.course_id:
            raise NotFoundError("course_id is required")

        session = await self._repository.find_by_course_id(dto.course_id)
        if session is None:
            raise NotFoundError(f"course_id '{dto.course_id}' not found or expired")

        selected = next((c for c in session.courses if c.course_id == dto.course_id), None)
        if selected is None:
            raise NotFoundError(f"course_id '{dto.course_id}' not found")

        transport = Transport(session.transport)
        places = await self._build_places(selected, transport)
        total_duration = sum(p.duration_minutes + (p.move_time_to_next_minutes or 0) for p in places)

        place_names = [p.name for p in places]
        title = f"{session.area}에서 즐기는 데이트 코스"
        description = f"{session.area}에서 {', '.join(place_names)}을(를) 즐기는 하루 코스입니다."

        other_courses = [
            self._to_other_course_dto(c, session, transport)
            for c in session.courses
            if c.course_id != dto.course_id
        ]

        return GetCourseDetailResponseDto(
            course_id=selected.course_id,
            grade=selected.grade,
            area=session.area,
            start_time=session.start_time,
            transport=session.transport,
            title=title,
            description=description,
            estimated_duration_minutes=total_duration,
            places=places,
            other_courses=other_courses,
        )

    async def _build_places(
        self,
        course: RecommendationCourseItemDto,
        transport: Transport,
    ) -> List[CourseDetailPlaceDto]:
        places = course.places
        move_times: List[Optional[int]] = list(
            await asyncio.gather(*[
                self._get_move_minutes(places[i], places[i + 1], transport)
                for i in range(len(places) - 1)
            ])
        ) + [None]

        return [
            CourseDetailPlaceDto(
                order=place.order,
                place_type=place.place_type,
                name=place.name,
                category=place.category,
                road_address=place.road_address,
                address=place.address,
                latitude=place.latitude,
                longitude=place.longitude,
                link=place.link,
                telephone=place.telephone,
                activity_type=place.activity_type,
                image_url=place.image_url,
                start_time=place.start_time,
                end_time=place.end_time,
                duration_minutes=place.duration_minutes,
                move_time_to_next_minutes=move_times[i],
                short_description=_SHORT_DESCRIPTIONS.get(
                    place.place_type, "특별한 장소에서 시간을 보내세요."
                ),
            )
            for i, place in enumerate(places)
        ]

    def _to_other_course_dto(
        self,
        course: RecommendationCourseItemDto,
        session: RecommendationSessionDto,
        transport: Transport,
    ) -> OtherCourseDto:
        route_summary = " > ".join(p.name for p in course.places)
        places = course.places
        total_duration = sum(p.duration_minutes for p in places)
        for i in range(len(places) - 1):
            total_duration += _travel_minutes(
                places[i].latitude, places[i].longitude,
                places[i + 1].latitude, places[i + 1].longitude,
                transport.speed_mps,
            )
        return OtherCourseDto(
            course_id=course.course_id,
            grade=course.grade,
            title=f"{session.area}에서 즐기는 데이트 코스",
            route_summary=route_summary,
            area=session.area,
            estimated_duration_minutes=total_duration,
        )
