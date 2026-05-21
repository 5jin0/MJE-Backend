from typing import List, Optional

from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.courses.domain.entity.course_entity import CourseEntity
from app.domains.courses.repository.course_repository_interface import CourseRepositoryInterface
from app.domains.courses.repository.mapper.course_mapper import to_orm, to_entity
from app.domains.courses.repository.orm.course_orm import CourseOrm


class MysqlCourseRepository(CourseRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, course: CourseEntity) -> None:
        orm = to_orm(course)
        self._session.add(orm)
        await self._session.flush()

    async def find_by_id(self, course_id: str) -> Optional[CourseEntity]:
        result = await self._session.execute(
            select(CourseOrm).where(CourseOrm.course_id == course_id)
        )
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        return to_entity(orm)

    async def find_by_session_id(self, session_id: str) -> List[CourseEntity]:
        grade_order = case({"best": 0}, value=CourseOrm.grade, else_=1)
        result = await self._session.execute(
            select(CourseOrm)
            .where(CourseOrm.session_id == session_id)
            .order_by(grade_order, CourseOrm.course_id)
        )
        return [to_entity(orm) for orm in result.scalars().all()]
