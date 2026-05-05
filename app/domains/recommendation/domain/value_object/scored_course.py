from dataclasses import dataclass
from typing import Set

from app.domains.recommendation.domain.service.course_ordering_service import OrderedCourseResult


@dataclass
class CourseScoreBreakdown:
    duration_score: int
    transport_score: int
    time_slot_score: int
    diversity_score: int
    duplicate_penalty: int

    @property
    def total(self) -> int:
        return (
            self.duration_score
            + self.transport_score
            + self.time_slot_score
            + self.diversity_score
            + self.duplicate_penalty
        )


@dataclass
class ScoredCourse:
    ordered_result: OrderedCourseResult
    score_breakdown: CourseScoreBreakdown

    @property
    def total_score(self) -> int:
        return self.score_breakdown.total

    def place_ids(self) -> Set[int]:
        return {p.place.id for p in self.ordered_result.places}
