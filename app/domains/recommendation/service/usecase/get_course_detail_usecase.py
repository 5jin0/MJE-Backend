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
)

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
    def __init__(self, repository: RecommendationSessionRepositoryInterface) -> None:
        self._repository = repository

    async def execute(self, dto: GetCourseDetailRequestDto) -> GetCourseDetailResponseDto:
        if not dto.course_id:
            raise NotFoundError("course_id is required")

        session = await self._repository.find_by_course_id(dto.course_id)
        if session is None:
            raise NotFoundError(f"course_id '{dto.course_id}' not found or expired")

        selected = next((c for c in session.courses if c.course_id == dto.course_id), None)
        if selected is None:
            raise NotFoundError(f"course_id '{dto.course_id}' not found")

        move_minutes = self._resolve_move_minutes(session.transport)
        places = self._build_places(selected, move_minutes)
        total_duration = sum(p.duration_minutes for p in places) + move_minutes * (len(places) - 1)

        place_names = [p.name for p in places]
        title = f"{session.area}에서 즐기는 데이트 코스"
        description = f"{session.area}에서 {', '.join(place_names)}을(를) 즐기는 하루 코스입니다."

        other_courses = [
            self._to_other_course_dto(c, session, move_minutes)
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

    def _build_places(
        self,
        course: RecommendationCourseItemDto,
        move_minutes: int,
    ) -> List[CourseDetailPlaceDto]:
        result = []
        for i, place in enumerate(course.places):
            is_last = i == len(course.places) - 1
            move_to_next: Optional[int] = None if is_last else move_minutes

            # Use pre-computed times if available, otherwise fall back to computing
            start_time = place.start_time
            end_time = place.end_time

            result.append(
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
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=place.duration_minutes,
                    move_time_to_next_minutes=move_to_next,
                    short_description=_SHORT_DESCRIPTIONS.get(
                        place.place_type, "특별한 장소에서 시간을 보내세요."
                    ),
                )
            )

        return result

    def _to_other_course_dto(
        self,
        course: RecommendationCourseItemDto,
        session: RecommendationSessionDto,
        move_minutes: int,
    ) -> OtherCourseDto:
        route_summary = " > ".join(p.name for p in course.places)
        total_duration = sum(p.duration_minutes for p in course.places) + move_minutes * (len(course.places) - 1)
        return OtherCourseDto(
            course_id=course.course_id,
            grade=course.grade,
            title=f"{session.area}에서 즐기는 데이트 코스",
            route_summary=route_summary,
            area=session.area,
            estimated_duration_minutes=total_duration,
        )

    def _resolve_move_minutes(self, transport_value: str) -> int:
        try:
            return Transport(transport_value).base_move_minutes
        except ValueError:
            return Transport.WALK.base_move_minutes
