from app.domains.courses.domain.entity.course_entity import CourseEntity, CoursePlace
from app.domains.courses.domain.value_object.recommendation_place import RecommendationPlace
from app.domains.courses.repository.orm.course_orm import CourseOrm, CoursePlaceOrm


def to_orm(entity: CourseEntity) -> CourseOrm:
    course_orm = CourseOrm(
        course_id=entity.course_id,
        grade=entity.grade,
        area=entity.area,
        start_time=entity.start_time,
        transport=entity.transport,
        title=entity.title,
        description=entity.description,
        estimated_duration_minutes=entity.estimated_duration_minutes,
    )
    course_orm.places = [_place_to_orm(entity.course_id, p) for p in entity.places]
    return course_orm


def to_entity(orm: CourseOrm) -> CourseEntity:
    places = [_place_to_entity(p) for p in sorted(orm.places, key=lambda p: p.place_order)]

    restaurant = _find_place(orm.places, "restaurant")
    cafe = _find_place(orm.places, "cafe")
    activity = _find_place(orm.places, "activity")

    return CourseEntity(
        course_id=orm.course_id,
        grade=orm.grade,
        area=orm.area,
        start_time=orm.start_time,
        transport=orm.transport,
        title=orm.title,
        description=orm.description,
        estimated_duration_minutes=orm.estimated_duration_minutes,
        restaurant=restaurant,
        cafe=cafe,
        activity=activity,
        places=places,
    )


def _place_to_orm(course_id: str, place: CoursePlace) -> CoursePlaceOrm:
    return CoursePlaceOrm(
        course_id=course_id,
        place_order=place.order,
        place_type=place.place_type,
        place_id=place.id,
        name=place.name,
        category=place.category,
        road_address=place.road_address,
        address=place.address,
        mapx=place.mapx,
        mapy=place.mapy,
        link=place.link,
        telephone=place.telephone,
        keyword=place.keyword,
        collected_at=place.collected_at,
        start_time=place.start_time,
        end_time=place.end_time,
        duration_minutes=place.duration_minutes,
        move_time_to_next_minutes=place.move_time_to_next_minutes,
    )


def _place_to_entity(orm: CoursePlaceOrm) -> CoursePlace:
    return CoursePlace(
        order=orm.place_order,
        place_type=orm.place_type,
        id=orm.place_id or 0,
        name=orm.name,
        category=orm.category or "",
        road_address=orm.road_address or "",
        address=orm.address or "",
        mapx=orm.mapx or "",
        mapy=orm.mapy or "",
        link=orm.link or "",
        telephone=orm.telephone or "",
        keyword=orm.keyword or "",
        collected_at=orm.collected_at or "",
        start_time=orm.start_time or "",
        end_time=orm.end_time or "",
        duration_minutes=orm.duration_minutes or 0,
        move_time_to_next_minutes=orm.move_time_to_next_minutes or 0,
    )


def _find_place(places: list[CoursePlaceOrm], place_type: str) -> RecommendationPlace:
    orm = next((p for p in places if p.place_type == place_type), None)
    if orm is None:
        return RecommendationPlace(
            id=0, name="", category="", road_address="", address="",
            mapx="", mapy="", link="", telephone="", keyword="", collected_at="",
        )
    return RecommendationPlace(
        id=orm.place_id or 0,
        name=orm.name,
        category=orm.category or "",
        road_address=orm.road_address or "",
        address=orm.address or "",
        mapx=orm.mapx or "",
        mapy=orm.mapy or "",
        link=orm.link or "",
        telephone=orm.telephone or "",
        keyword=orm.keyword or "",
        collected_at=orm.collected_at or "",
    )
