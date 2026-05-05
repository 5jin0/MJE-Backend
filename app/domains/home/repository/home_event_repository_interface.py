from abc import ABC, abstractmethod

from app.domains.home.domain.entity.home_event_entity import HomeEventEntity


class HomeEventRepositoryInterface(ABC):
    @abstractmethod
    async def save(self, entity: HomeEventEntity) -> None: ...
