from dataclasses import dataclass
from typing import List

from app.domains.recommendation.domain.entity.course_candidate import CourseCandidate
from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace
from app.domains.recommendation.domain.value_object.place_schedule import PlaceSchedule
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.domain.value_object.transport import Transport

_TARGET_MIN = 270
_TARGET_MAX = 360
_ALLOW_MIN = 220
_ALLOW_MAX = 420

_DEFAULT_ACTIVITY_DURATION = 120


@dataclass
class DurationResult:
    place_schedules: List[PlaceSchedule]
    total_duration_minutes: int
    duration_score: float
    is_valid: bool


class DurationCalculatorService:
    def calculate(
        self,
        candidate: CourseCandidate,
        start_time: str,
        transport: Transport,
    ) -> DurationResult:
        return self.calculate_for_places(
            [candidate.restaurant, candidate.cafe, candidate.activity],
            start_time,
            transport,
        )

    def calculate_for_places(
        self,
        places: List[CandidatePlace],
        start_time: str,
        transport: Transport,
    ) -> DurationResult:
        move_time = transport.base_move_minutes
        schedules: List[PlaceSchedule] = []
        current_time = start_time

        for i, place in enumerate(places):
            duration = self._get_duration(place)
            is_last = i == len(places) - 1
            move_to_next = 0 if is_last else move_time

            end_time = self._add_minutes(current_time, duration)
            schedules.append(PlaceSchedule(
                start_time=current_time,
                end_time=end_time,
                duration_minutes=duration,
                move_time_to_next_minutes=move_to_next,
            ))
            current_time = self._add_minutes(end_time, move_to_next)

        total = sum(s.duration_minutes + s.move_time_to_next_minutes for s in schedules)
        is_valid = _ALLOW_MIN <= total <= _ALLOW_MAX
        score = self._calculate_score(total)

        return DurationResult(
            place_schedules=schedules,
            total_duration_minutes=total,
            duration_score=score,
            is_valid=is_valid,
        )

    def _get_duration(self, place: CandidatePlace) -> int:
        if place.place_type == PlaceType.RESTAURANT:
            return 80
        if place.place_type == PlaceType.CAFE:
            return 60
        if place.activity_kind is not None:
            return place.activity_kind.duration_minutes
        return _DEFAULT_ACTIVITY_DURATION

    def _calculate_score(self, total: int) -> float:
        if total < _ALLOW_MIN or total > _ALLOW_MAX:
            return 0.0
        if _TARGET_MIN <= total <= _TARGET_MAX:
            return 1.0
        if total < _TARGET_MIN:
            return (total - _ALLOW_MIN) / (_TARGET_MIN - _ALLOW_MIN)
        return (_ALLOW_MAX - total) / (_ALLOW_MAX - _TARGET_MAX)

    @staticmethod
    def _add_minutes(time_str: str, minutes: int) -> str:
        h, m = map(int, time_str.split(":"))
        total = h * 60 + m + minutes
        return f"{total // 60 % 24:02d}:{total % 60:02d}"
