from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.courses.domain.entity.courses_event_entity import CoursesEventEntity
from app.domains.courses.repository.courses_event_repository_interface import CoursesEventRepositoryInterface
from app.domains.courses.repository.mapper.courses_event_mapper import to_orm


class MysqlCoursesEventRepository(CoursesEventRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, entity: CoursesEventEntity) -> None:
        orm = to_orm(entity)
        self._session.add(orm)
        await self._session.flush()
