from typing import List

from pydantic import BaseModel

from app.domains.courses.service.dto.response.create_recommendation_response_dto import (
    CreateRecommendationResponseDto,
)


class RecommendationPlaceResponseForm(BaseModel):
    id: int
    name: str
    category: str
    road_address: str
    address: str
    mapx: str
    mapy: str
    link: str
    telephone: str
    keyword: str
    collected_at: str


class CourseRecommendationItemResponseForm(BaseModel):
    course_id: str
    grade: str
    restaurant: RecommendationPlaceResponseForm
    cafe: RecommendationPlaceResponseForm
    activity: RecommendationPlaceResponseForm


class CreateRecommendationResponseForm(BaseModel):
    courses: List[CourseRecommendationItemResponseForm]
    shortage_reasons: List[str]

    @classmethod
    def from_response(cls, dto: CreateRecommendationResponseDto) -> "CreateRecommendationResponseForm":
        courses = [
            CourseRecommendationItemResponseForm(
                course_id=item.course_id,
                grade=item.grade,
                restaurant=RecommendationPlaceResponseForm(**vars(item.restaurant)),
                cafe=RecommendationPlaceResponseForm(**vars(item.cafe)),
                activity=RecommendationPlaceResponseForm(**vars(item.activity)),
            )
            for item in dto.courses
        ]
        return cls(courses=courses, shortage_reasons=dto.shortage_reasons)
