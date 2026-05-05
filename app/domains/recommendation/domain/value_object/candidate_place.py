from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from app.domains.recommendation.domain.value_object.place_type import PlaceType

if TYPE_CHECKING:
    from app.domains.recommendation.domain.value_object.activity_type import ActivityKind


@dataclass(frozen=True)
class CandidatePlace:
    id: int
    name: str
    category: str
    road_address: str
    address: str
    mapx: str
    mapy: str
    link: str
    telephone: str
    keyword: str
    collected_at: str
    place_type: PlaceType
    activity_kind: Optional[ActivityKind] = field(default=None)
