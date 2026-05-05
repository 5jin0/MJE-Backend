from dataclasses import dataclass, field
from typing import List


@dataclass
class RecommendationPlaceDto:
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


@dataclass
class CourseRecommendationItemDto:
    course_id: str
    grade: str
    restaurant: RecommendationPlaceDto
    cafe: RecommendationPlaceDto
    activity: RecommendationPlaceDto


@dataclass
class CreateRecommendationResponseDto:
    courses: List[CourseRecommendationItemDto]
    shortage_reasons: List[str] = field(default_factory=list)
