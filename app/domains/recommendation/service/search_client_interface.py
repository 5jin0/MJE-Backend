from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class RawPlaceResult:
    title: str
    link: str
    category: str
    description: str
    telephone: str
    address: str
    road_address: str
    mapx: str
    mapy: str


class SearchClientInterface(ABC):
    @abstractmethod
    def search_places(self, query: str, display: int = 5) -> List[RawPlaceResult]: ...
