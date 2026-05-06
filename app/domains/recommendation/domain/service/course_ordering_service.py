from dataclasses import dataclass
from typing import List

from app.domains.recommendation.domain.entity.course_candidate import CourseCandidate
from app.domains.recommendation.domain.service.duration_calculator_service import (
    DurationCalculatorService,
    DurationResult,
)
from app.domains.recommendation.domain.value_object.ordered_place import OrderedPlace
from app.domains.recommendation.domain.value_object.transport import Transport


@dataclass
class OrderedCourseResult:
    places: List[OrderedPlace]
    total_duration_minutes: int
    duration_score: float
    is_valid: bool


class CourseOrderingService:
    def __init__(self) -> None:
        self._duration_calculator = DurationCalculatorService()

    def apply_order(
        self,
        candidate: CourseCandidate,
        start_time: str,
        transport: Transport,
    ) -> OrderedCourseResult:
        duration_result: DurationResult = self._duration_calculator.calculate_for_places(
            candidate.places, start_time, transport
        )

        places = [
            OrderedPlace(
                order=i + 1,
                place=candidate.places[i],
                schedule=duration_result.place_schedules[i],
            )
            for i in range(len(candidate.places))
        ]

        return OrderedCourseResult(
            places=places,
            total_duration_minutes=duration_result.total_duration_minutes,
            duration_score=duration_result.duration_score,
            is_valid=duration_result.is_valid,
        )
