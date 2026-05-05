from abc import ABC, abstractmethod

from app.domains.courses.domain.entity.courses_event_entity import CoursesEventEntity


class CoursesEventRepositoryInterface(ABC):
    @abstractmethod
    async def save(self, entity: CoursesEventEntity) -> None: ...
