from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domains.recommendation.domain.value_object.transport import Transport


@dataclass
class RouteRequest:
    from_mapx: str
    from_mapy: str
    to_mapx: str
    to_mapy: str
    transport: Transport


@dataclass
class RouteInfo:
    from_mapx: str
    from_mapy: str
    to_mapx: str
    to_mapy: str
    transport: Transport
    duration_minutes: int
    distance_meters: int
    is_fallback: bool


class MapClientInterface(ABC):
    @abstractmethod
    def get_route(self, request: RouteRequest) -> RouteInfo: ...
