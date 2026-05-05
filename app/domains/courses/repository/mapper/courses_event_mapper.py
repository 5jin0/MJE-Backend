from app.domains.courses.domain.entity.courses_event_entity import CoursesEventEntity
from app.domains.courses.domain.events.courses_event import CoursesEventType
from app.domains.courses.repository.orm.courses_event_orm import CoursesEventOrm


def to_orm(entity: CoursesEventEntity) -> CoursesEventOrm:
    return CoursesEventOrm(
        event_name=entity.event_name.value,
        session_id=entity.session_id,
        timestamp=entity.timestamp,
        page_path=entity.page_path,
    )


def to_entity(orm: CoursesEventOrm) -> CoursesEventEntity:
    return CoursesEventEntity(
        id=orm.id,
        event_name=CoursesEventType(orm.event_name),
        session_id=orm.session_id,
        timestamp=orm.timestamp,
        page_path=orm.page_path,
    )
