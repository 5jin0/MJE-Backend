from abc import ABC, abstractmethod
from typing import Optional

from app.domains.recommendation.service.place_candidate_collector import PlaceCandidateCollection


class CandidateCacheInterface(ABC):
    @abstractmethod
    async def get(self, area: str) -> Optional[PlaceCandidateCollection]: ...

    @abstractmethod
    async def set(self, area: str, collection: PlaceCandidateCollection) -> None: ...
