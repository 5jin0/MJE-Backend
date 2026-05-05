from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.home.domain.entity.home_event_entity import HomeEventEntity
from app.domains.home.repository.home_event_repository_interface import HomeEventRepositoryInterface
from app.domains.home.repository.mapper.home_event_mapper import to_orm


class MysqlHomeEventRepository(HomeEventRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, entity: HomeEventEntity) -> None:
        orm = to_orm(entity)
        self._session.add(orm)
        await self._session.flush()
