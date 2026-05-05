from abc import ABC, abstractmethod
from typing import Optional, Tuple


class GeocodingClientInterface(ABC):
    @abstractmethod
    def geocode(self, area: str) -> Optional[Tuple[float, float]]:
        """Returns (longitude, latitude) in WGS84, or None if geocoding fails."""
