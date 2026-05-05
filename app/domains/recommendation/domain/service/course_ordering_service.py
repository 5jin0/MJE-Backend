from dataclasses import dataclass
from typing import Dict, List

from app.domains.recommendation.domain.entity.course_candidate import CourseCandidate
from app.domains.recommendation.domain.service.duration_calculator_service import (
    DurationCalculatorService,
    DurationResult,
)
from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace
from app.domains.recommendation.domain.value_object.ordered_place import OrderedPlace
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot
from app.domains.recommendation.domain.value_object.transport import Transport

_VISIT_ORDER: Dict[TimeSlot, List[PlaceType]] = {
    TimeSlot.LUNCH:     [PlaceType.RESTAURANT, PlaceType.CAFE,       PlaceType.ACTIVITY],
    TimeSlot.AFTERNOON: [PlaceType.CAFE,       PlaceType.ACTIVITY,   PlaceType.RESTAURANT],
    TimeSlot.EVENING:   [PlaceType.RESTAURANT, PlaceType.ACTIVITY,   PlaceType.CAFE],
    TimeSlot.NIGHT:     [PlaceType.RESTAURANT, PlaceType.ACTIVITY,   PlaceType.CAFE],
}


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
        time_slot = TimeSlot.from_start_time(start_time)
        place_type_order = _VISIT_ORDER[time_slot]

        place_map: Dict[PlaceType, CandidatePlace] = {
            PlaceType.RESTAURANT: candidate.restaurant,
            PlaceType.CAFE: candidate.cafe,
            PlaceType.ACTIVITY: candidate.activity,
        }
        ordered_places = [place_map[pt] for pt in place_type_order]

        duration_result: DurationResult = self._duration_calculator.calculate_for_places(
            ordered_places, start_time, transport
        )

        places = [
            OrderedPlace(
                order=i + 1,
                place=ordered_places[i],
                schedule=duration_result.place_schedules[i],
            )
            for i in range(len(ordered_places))
        ]

        return OrderedCourseResult(
            places=places,
            total_duration_minutes=duration_result.total_duration_minutes,
            duration_score=duration_result.duration_score,
            is_valid=duration_result.is_valid,
        )
