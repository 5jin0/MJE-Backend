from typing import Dict, Optional

from app.domains.courses.domain.entity.course_entity import CourseEntity
from app.domains.courses.repository.course_repository_interface import CourseRepositoryInterface

_store: Dict[str, CourseEntity] = {}


class InMemoryCourseRepository(CourseRepositoryInterface):
    def save(self, course: CourseEntity) -> None:
        _store[course.course_id] = course

    def find_by_id(self, course_id: str) -> Optional[CourseEntity]:
        return _store.get(course_id)


_instance = InMemoryCourseRepository()


def get_course_repository() -> CourseRepositoryInterface:
    return _instance
