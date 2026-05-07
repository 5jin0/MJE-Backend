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
                places=[
                    RecommendationPlaceDto(
                        order=p["order"],
                        place_type=p["place_type"],
                        name=p["name"],
                        category=p["category"],
                        road_address=p.get("road_address", ""),
                        address=p.get("address", ""),
                        latitude=p.get("latitude", 0.0),
                        longitude=p.get("longitude", 0.0),
                        link=p.get("link", ""),
                        telephone=p.get("telephone", ""),
                        activity_type=p.get("activity_type"),
                        duration_minutes=p.get("duration_minutes", 0),
                        start_time=p.get("start_time", ""),
                        end_time=p.get("end_time", ""),
                        image_url=p.get("image_url"),
                    )
                    for p in item["places"]
                ],
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
