from typing import List

from app.domains.recommendation.domain.entity.course_candidate import Course, CourseCandidate, CoursePlace
from app.domains.recommendation.domain.service.duration_calculator_service import DurationCalculatorService
from app.domains.recommendation.domain.value_object.activity_type import ActivityType
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot
from app.domains.recommendation.domain.value_object.transport import Transport

_SLOT_NIGHTLIFE_BONUS = {
    TimeSlot.MORNING: -0.3,
    TimeSlot.LUNCH: -0.2,
    TimeSlot.AFTERNOON: -0.1,
    TimeSlot.EVENING: 0.2,
    TimeSlot.LATE_NIGHT: 0.3,
}

_SLOT_DAYTIME_BONUS = {
    TimeSlot.MORNING: 0.2,
    TimeSlot.LUNCH: 0.3,
    TimeSlot.AFTERNOON: 0.2,
    TimeSlot.EVENING: -0.1,
    TimeSlot.LATE_NIGHT: -0.2,
}


class CourseScorerService:
    def __init__(self) -> None:
        self._duration_service = DurationCalculatorService()

    def score_and_build(
        self,
        candidate: CourseCandidate,
        start_time: str,
        transport: Transport,
        time_slot: TimeSlot,
    ) -> Course:
        course_places = self._duration_service.schedule(candidate, start_time, transport)
        total_score = self._compute_score(course_places, time_slot, transport)
        is_valid = self._duration_service.is_valid(course_places)

        return Course(
            places=course_places,
            total_score=total_score,
            is_valid=is_valid,
        )

    def _compute_score(
        self,
        course_places: List[CoursePlace],
        time_slot: TimeSlot,
        transport: Transport,
    ) -> float:
        places = [cp.place for cp in course_places]

        place_score = sum(p.score for p in places) / len(places) if places else 0.0

        duration_score = self._duration_service.duration_score(course_places)

        time_bonus = self._time_slot_bonus(places, time_slot)

        raw = 0.4 * place_score + 0.3 * duration_score + 0.3 * (0.5 + time_bonus)
        return max(0.0, min(1.0, raw))

    def _time_slot_bonus(self, places, time_slot: TimeSlot) -> float:
        activity_places = [p for p in places if p.category == PlaceType.ACTIVITY.value]
        if not activity_places:
            return 0.0

        has_nightlife = any(
            p.activity_type == ActivityType.NIGHTLIFE.value
            for p in activity_places
        )

        bonus_map = _SLOT_NIGHTLIFE_BONUS if has_nightlife else _SLOT_DAYTIME_BONUS
        return bonus_map.get(time_slot, 0.0)
