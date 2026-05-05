from typing import Dict, Optional, Set

from app.domains.recommendation.domain.service.course_ordering_service import OrderedCourseResult
from app.domains.recommendation.domain.value_object.activity_type import ActivityType
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.domain.value_object.scored_course import (
    CourseScoreBreakdown,
    ScoredCourse,
)
from app.domains.recommendation.domain.value_object.time_slot import TimeSlot
from app.domains.recommendation.domain.value_object.transport import Transport

_TIMESLOT_ACTIVITY_SCORES: Dict[TimeSlot, Dict[ActivityType, int]] = {
    TimeSlot.LUNCH:     {ActivityType.CORE_ACTIVITY: 5, ActivityType.SUB_ACTIVITY: 2},
    TimeSlot.AFTERNOON: {ActivityType.CORE_ACTIVITY: 5, ActivityType.SUB_ACTIVITY: 3},
    TimeSlot.EVENING:   {ActivityType.CORE_ACTIVITY: 4, ActivityType.SUB_ACTIVITY: 5},
    TimeSlot.NIGHT:     {ActivityType.CORE_ACTIVITY: 2, ActivityType.SUB_ACTIVITY: 5},
}

_TRANSPORT_SCORES: Dict[Transport, int] = {
    Transport.WALK: 8,
    Transport.PUBLIC_TRANSIT: 5,
    Transport.CAR: 3,
}


class CourseScorerService:
    def score(
        self,
        ordered_result: OrderedCourseResult,
        time_slot: TimeSlot,
        transport: Transport,
        best_place_ids: Optional[Set[int]] = None,
    ) -> ScoredCourse:
        breakdown = CourseScoreBreakdown(
            duration_score=self._duration_score(ordered_result.total_duration_minutes),
            transport_score=_TRANSPORT_SCORES[transport],
            time_slot_score=self._time_slot_score(time_slot, ordered_result),
            diversity_score=self._diversity_score(ordered_result),
            duplicate_penalty=self._duplicate_penalty(ordered_result, best_place_ids),
        )
        return ScoredCourse(ordered_result=ordered_result, score_breakdown=breakdown)

    def _duration_score(self, total: int) -> int:
        if 300 <= total <= 360:
            return 10
        if 270 <= total <= 299 or 361 <= total <= 390:
            return 5
        if 391 <= total <= 420:
            return 2
        return 0

    def _time_slot_score(self, time_slot: TimeSlot, ordered_result: OrderedCourseResult) -> int:
        activity_place = next(
            (p for p in ordered_result.places if p.place_type == PlaceType.ACTIVITY), None
        )
        if activity_place is None:
            return 3
        if activity_place.place.activity_kind is not None:
            activity_type = activity_place.place.activity_kind.activity_type
            return _TIMESLOT_ACTIVITY_SCORES[time_slot][activity_type]
        return 3

    def _diversity_score(self, ordered_result: OrderedCourseResult) -> int:
        activity_place = next(
            (p for p in ordered_result.places if p.place_type == PlaceType.ACTIVITY), None
        )
        if activity_place is None:
            return 1
        return 3 if activity_place.place.activity_kind is not None else 1

    def _duplicate_penalty(
        self,
        ordered_result: OrderedCourseResult,
        best_place_ids: Optional[Set[int]],
    ) -> int:
        penalty = 0
        place_ids = [p.place.id for p in ordered_result.places]

        if len(place_ids) != len(set(place_ids)):
            penalty -= 10

        if best_place_ids:
            overlap_count = len(set(place_ids) & best_place_ids)
            penalty -= overlap_count * 5

        return penalty
