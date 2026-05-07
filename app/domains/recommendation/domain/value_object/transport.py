from enum import Enum


class Transport(Enum):
    WALK = "walk"
    PUBLIC_TRANSIT = "public_transit"
    CAR = "car"

    @property
    def speed_mps(self) -> float:
        return {
            Transport.WALK: 1.39,
            Transport.PUBLIC_TRANSIT: 5.0,
            Transport.CAR: 8.33,
        }[self]

    @property
    def max_travel_minutes(self) -> int:
        return {
            Transport.WALK: 10,
            Transport.PUBLIC_TRANSIT: 20,
            Transport.CAR: 30,
        }[self]

    @property
    def needs_parking(self) -> bool:
        return self == Transport.CAR

    # 기존 코드 호환
    @property
    def base_move_minutes(self) -> int:
        return self.max_travel_minutes

    @classmethod
    def from_str(cls, value: str) -> "Transport":
        return cls(value)
