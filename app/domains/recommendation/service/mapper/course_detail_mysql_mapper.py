from typing import List

from app.domains.courses.domain.entity.course_entity import CourseEntity
from app.domains.recommendation.service.dto.response.get_course_detail_response_dto import (
    CourseDetailPlaceDto,
    GetCourseDetailResponseDto,
    OtherCourseDto,
)


def build_course_detail_from_entity(
    course_id: str,
    entity: CourseEntity,
    other_entities: List[CourseEntity] = [],
) -> GetCourseDetailResponseDto:
    places = [
        CourseDetailPlaceDto(
            order=p.order,
            place_type=p.place_type,
            name=p.name,
            category=p.category,
            road_address=p.road_address,
            address=p.address,
            latitude=_parse_coord(p.mapy),
            longitude=_parse_coord(p.mapx),
            link=p.link,
            telephone=p.telephone,
            activity_type=None,
            image_url=None,
            start_time=p.start_time,
            end_time=p.end_time,
            duration_minutes=p.duration_minutes,
            move_time_to_next_minutes=p.move_time_to_next_minutes,
            short_description="",
        )
        for p in sorted(entity.places, key=lambda x: x.order)
    ]

    other_courses = [
        OtherCourseDto(
            course_id=o.course_id,
            grade=o.grade,
            title=o.title,
            route_summary=" > ".join(p.name for p in sorted(o.places, key=lambda x: x.order)),
            area=o.area,
            estimated_duration_minutes=o.estimated_duration_minutes,
        )
        for o in other_entities
        if o.course_id != course_id
    ]

    return GetCourseDetailResponseDto(
        course_id=entity.course_id,
        grade=entity.grade,
        area=entity.area,
        start_time=entity.start_time,
        transport=entity.transport,
        title=entity.title,
        description=entity.description,
        estimated_duration_minutes=entity.estimated_duration_minutes,
        places=places,
        other_courses=other_courses,
    )


def _parse_coord(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
