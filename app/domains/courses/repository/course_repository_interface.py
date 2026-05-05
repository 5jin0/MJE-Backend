from abc import ABC, abstractmethod
from typing import Optional

from app.domains.courses.domain.entity.course_entity import CourseEntity


class CourseRepositoryInterface(ABC):
    @abstractmethod
    def save(self, course: CourseEntity) -> None: ...

    @abstractmethod
    def find_by_id(self, course_id: str) -> Optional[CourseEntity]: ...
