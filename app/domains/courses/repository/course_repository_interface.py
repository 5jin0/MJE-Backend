from abc import ABC, abstractmethod
from typing import List, Optional

from app.domains.courses.domain.entity.course_entity import CourseEntity


class CourseRepositoryInterface(ABC):
    @abstractmethod
    async def save(self, course: CourseEntity) -> None: ...

    @abstractmethod
    async def find_by_id(self, course_id: str) -> Optional[CourseEntity]: ...

    @abstractmethod
    async def find_by_session_id(self, session_id: str) -> List[CourseEntity]: ...
