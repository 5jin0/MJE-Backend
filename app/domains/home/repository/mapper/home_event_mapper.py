from app.domains.home.domain.entity.home_event_entity import HomeEventEntity
from app.domains.home.domain.events.home_event import HomeEventType
from app.domains.home.repository.orm.home_event_orm import HomeEventOrm


def to_orm(entity: HomeEventEntity) -> HomeEventOrm:
    return HomeEventOrm(
        event_name=entity.event_name.value,
        session_id=entity.session_id,
        timestamp=entity.timestamp,
        page_path=entity.page_path,
    )


def to_entity(orm: HomeEventOrm) -> HomeEventEntity:
    return HomeEventEntity(
        id=orm.id,
        event_name=HomeEventType(orm.event_name),
        session_id=orm.session_id,
        timestamp=orm.timestamp,
        page_path=orm.page_path,
    )
