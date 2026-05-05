from typing import List, Optional

from pydantic import BaseModel

from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    GetRecommendationResponseDto,
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
    image_url: Optional[str]


class RecommendationCourseItemResponseForm(BaseModel):
    course_id: str
    grade: str
    restaurant: RecommendationPlaceResponseForm
    cafe: RecommendationPlaceResponseForm
    activity: RecommendationPlaceResponseForm
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
                restaurant=RecommendationPlaceResponseForm(**vars(item.restaurant)),
                cafe=RecommendationPlaceResponseForm(**vars(item.cafe)),
                activity=RecommendationPlaceResponseForm(**vars(item.activity)),
                image_url=item.image_url,
            )
            for item in dto.courses
        ]
        return cls(courses=courses, shortage_reasons=dto.shortage_reasons)
