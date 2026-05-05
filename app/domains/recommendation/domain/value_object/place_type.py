from enum import Enum


class PlaceType(Enum):
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    ACTIVITY = "activity"

    @property
    def default_duration_minutes(self) -> int:
        _durations = {
            PlaceType.RESTAURANT: 80,
            PlaceType.CAFE: 60,
            PlaceType.ACTIVITY: 120,
        }
        return _durations[self]
