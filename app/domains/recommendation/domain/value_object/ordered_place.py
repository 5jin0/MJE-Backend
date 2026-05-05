from __future__ import annotations

from dataclasses import dataclass

from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace
from app.domains.recommendation.domain.value_object.place_schedule import PlaceSchedule
from app.domains.recommendation.domain.value_object.place_type import PlaceType


@dataclass(frozen=True)
class OrderedPlace:
    order: int
    place: CandidatePlace
    schedule: PlaceSchedule

    @property
    def place_type(self) -> PlaceType:
        return self.place.place_type

    @property
    def start_time(self) -> str:
        return self.schedule.start_time

    @property
    def end_time(self) -> str:
        return self.schedule.end_time

    @property
    def duration_minutes(self) -> int:
        return self.schedule.duration_minutes

    @property
    def move_time_to_next_minutes(self) -> int:
        return self.schedule.move_time_to_next_minutes
