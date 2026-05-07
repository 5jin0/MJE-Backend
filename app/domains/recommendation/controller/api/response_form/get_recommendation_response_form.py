from typing import List, Optional

from pydantic import BaseModel

from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    GetRecommendationResponseDto,
)


class RecommendationPlaceResponseForm(BaseModel):
    order: int
    place_type: str
    name: str
    category: str
    road_address: str
    address: str
    latitude: float
    longitude: float
    link: str
    telephone: str
    activity_type: Optional[str]
    duration_minutes: int
    start_time: str
    end_time: str
    image_url: Optional[str]


class RecommendationCourseItemResponseForm(BaseModel):
    course_id: str
    grade: str
    places: List[RecommendationPlaceResponseForm]
    image_url: Optional[str]


class GetRecommendationResponseForm(BaseModel):
    courses: List[RecommendationCourseItemResponseForm]
    shortage_reasons: List[str]

    @classmethod
    def from_response(cls, dto: GetRecommendationResponseDto) -> "GetRecommendationResponseForm":
        courses = [
            RecommendationCourseItemResponseForm(
                course_id=item.course_id,
                grade=item.grade,
                places=[
                    RecommendationPlaceResponseForm(
                        order=p.order,
                        place_type=p.place_type,
                        name=p.name,
                        category=p.category,
                        road_address=p.road_address,
                        address=p.address,
                        latitude=p.latitude,
                        longitude=p.longitude,
                        link=p.link,
                        telephone=p.telephone,
                        activity_type=p.activity_type,
                        duration_minutes=p.duration_minutes,
                        start_time=p.start_time,
                        end_time=p.end_time,
                        image_url=p.image_url,
                    )
                    for p in item.places
                ],
                image_url=item.image_url,
            )
            for item in dto.courses
        ]
        return cls(courses=courses, shortage_reasons=dto.shortage_reasons)
