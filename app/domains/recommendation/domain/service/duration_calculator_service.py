from typing import List, Optional

from app.domains.recommendation.domain.entity.course_candidate import CourseCandidate, CoursePlace
from app.domains.recommendation.domain.value_object.activity_type import ActivityType
from app.domains.recommendation.domain.value_object.place import Place
from app.domains.recommendation.domain.value_object.place_type import PlaceType
from app.domains.recommendation.domain.value_object.transport import Transport

_TARGET_MIN = 270
_TARGET_MAX = 360
_ALLOW_MIN = 220
_ALLOW_MAX = 420

_ACTIVITY_TYPE_DURATIONS = {
    ActivityType.MOVIE.value: 130,
    ActivityType.EXHIBITION.value: 90,
    ActivityType.EXPERIENCE.value: 90,
    ActivityType.SHOPPING.value: 90,
    ActivityType.NIGHTLIFE.value: 90,
    ActivityType.WALK.value: 60,
    ActivityType.PARK.value: 60,
}


def _add_minutes(time_str: str, minutes: int) -> str:
    h, m = map(int, time_str.split(":"))
    total = h * 60 + m + minutes
    return f"{total // 60 % 24:02d}:{total % 60:02d}"


def _duration_score(total: int) -> float:
    if total < _ALLOW_MIN or total > _ALLOW_MAX:
        return 0.0
    if _TARGET_MIN <= total <= _TARGET_MAX:
        return 1.0
    if total < _TARGET_MIN:
        return (total - _ALLOW_MIN) / (_TARGET_MIN - _ALLOW_MIN)
    return (_ALLOW_MAX - total) / (_ALLOW_MAX - _TARGET_MAX)


def _get_duration(place: Place) -> int:
    if place.category == PlaceType.RESTAURANT.value:
        return 90
    if place.category == PlaceType.CAFE.value:
        return 60
    if place.activity_type:
        return _ACTIVITY_TYPE_DURATIONS.get(place.activity_type, 120)
    return 120


class DurationCalculatorService:
    def schedule(
        self,
        candidate: CourseCandidate,
        start_time: str,
        transport: Transport,
    ) -> List[CoursePlace]:
        return self.schedule_places(candidate.places, start_time, transport)

    def schedule_places(
        self,
        places: List[Place],
        start_time: str,
        transport: Transport,
    ) -> List[CoursePlace]:
        result: List[CoursePlace] = []
        current_time = start_time

        for i, place in enumerate(places):
            duration = _get_duration(place)
            is_last = i == len(places) - 1
            if is_last:
                move_to_next = 0
            else:
                distance_m = place.distance_to(places[i + 1])
                move_to_next = max(1, round(distance_m / transport.speed_mps / 60))
            end_time = _add_minutes(current_time, duration)

            result.append(CoursePlace(
                place=place,
                order=i + 1,
                duration_minutes=duration,
                move_minutes_to_next=move_to_next,
                start_time=current_time,
                end_time=end_time,
            ))
            current_time = _add_minutes(end_time, move_to_next)

        return result

    def total_duration(self, course_places: List[CoursePlace]) -> int:
        return sum(cp.duration_minutes + cp.move_minutes_to_next for cp in course_places)

    def is_valid(self, course_places: List[CoursePlace], transport: Optional[Transport] = None) -> bool:
        total = self.total_duration(course_places)
        if not (_ALLOW_MIN <= total <= _ALLOW_MAX):
            return False
        if transport is not None:
            return all(
                cp.move_minutes_to_next <= transport.max_move_minutes
                for cp in course_places
            )
        return True

    def duration_score(self, course_places: List[CoursePlace]) -> float:
        return _duration_score(self.total_duration(course_places))
