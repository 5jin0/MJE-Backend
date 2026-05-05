from dataclasses import dataclass, field
from typing import Any, List

from app.domains.recommendation.service.dto.response.get_recommendation_response_dto import (
    RecommendationCourseItemDto,
    RecommendationPlaceDto,
)


@dataclass
class RecommendationSessionDto:
    area: str
    start_time: str
    transport: str
    courses: List[RecommendationCourseItemDto] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecommendationSessionDto":
        courses = [
            RecommendationCourseItemDto(
                course_id=item["course_id"],
                grade=item["grade"],
                restaurant=RecommendationPlaceDto(**item["restaurant"]),
                cafe=RecommendationPlaceDto(**item["cafe"]),
                activity=RecommendationPlaceDto(**item["activity"]),
                image_url=item.get("image_url"),
            )
            for item in data.get("courses", [])
        ]

        return cls(
            area=data["area"],
            start_time=data["start_time"],
            transport=data["transport"],
            courses=courses,
        )
