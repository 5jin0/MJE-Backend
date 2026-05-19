import uuid
from typing import List, Optional

from app.domains.recommendation.domain.entity.course_candidate import Course
from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    GetRecommendationResponseDto,
    RecommendationCourseItemDto,
    RecommendationPlaceDto,
)


class RecommendationResponseMapper:
    def to_response_dto(
        self,
        best: Optional[Course],
        optionals: List[Course],
        shortage_reasons: List[str],
    ) -> GetRecommendationResponseDto:
        courses: List[RecommendationCourseItemDto] = []

        if best is not None:
            courses.append(self._to_course_item(best, "best"))

        for optional in optionals:
            courses.append(self._to_course_item(optional, "optional"))

        return GetRecommendationResponseDto(
            courses=courses,
            shortage_reasons=shortage_reasons,
        )

    def _to_course_item(self, course: Course, grade: str) -> RecommendationCourseItemDto:
        course_id = course.course_id or str(uuid.uuid4())
        return RecommendationCourseItemDto(
            course_id=course_id,
            grade=grade,
            places=[self._to_place_dto(cp) for cp in course.places],
        )

    def _to_place_dto(self, course_place) -> RecommendationPlaceDto:
        p = course_place.place
        return RecommendationPlaceDto(
            order=course_place.order,
            place_type=p.category,
            name=p.name,
            category=p.category,
            road_address=p.road_address,
            address=p.address,
            latitude=p.latitude,
            longitude=p.longitude,
            link=p.link,
            telephone=p.telephone,
            activity_type=p.activity_type,
            duration_minutes=course_place.duration_minutes,
            start_time=course_place.start_time,
            end_time=course_place.end_time,
            image_url=p.image_url,
        )
