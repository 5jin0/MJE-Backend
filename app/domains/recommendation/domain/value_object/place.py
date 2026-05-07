from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import time
from typing import List, Optional


_HTML_TAG = re.compile(r"<[^>]+>")
_HTML_ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'"}


def _clean_html(text: str) -> str:
    text = _HTML_TAG.sub("", text)
    for ent, char in _HTML_ENTITIES.items():
        text = text.replace(ent, char)
    return text.strip()


@dataclass
class Place:
    name: str
    area: str
    category: str           # "restaurant" | "cafe" | "activity"
    address: str
    road_address: str
    latitude: float
    longitude: float
    search_rank: int
    keywords: List[str] = field(default_factory=list)
    activity_type: Optional[str] = None
    category_confidence: float = 1.0
    image_url: Optional[str] = None
    rating: float = 0.0
    has_parking: bool = False
    business_close_time: Optional[time] = None
    score: float = 0.0
    is_franchise: bool = False
    place_key: str = ""
    main_description: str = ""
    brief_description: str = ""
    link: str = ""
    telephone: str = ""

    def is_open_at_slot_start(self, slot_start_minutes: int) -> bool:
        if self.business_close_time is None:
            return True
        close = self.business_close_time.hour * 60 + self.business_close_time.minute
        if close < 120:  # 02:00 미만이면 심야 영업 간주
            return True
        return (close - slot_start_minutes) > 60

    def distance_to(self, other: "Place") -> float:
        """haversine 거리 (meters)"""
        R = 6_371_000.0
        lat1 = math.radians(self.latitude)
        lat2 = math.radians(other.latitude)
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    @classmethod
    def from_kakao(cls, doc: dict, category: str, search_rank: int) -> "Place":
        raw_name = _clean_html(doc.get("place_name", ""))
        road_addr = doc.get("road_address_name", "")
        address = doc.get("address_name", "")
        tokens = road_addr.split() if road_addr else address.split()
        area = tokens[1] if len(tokens) > 1 else (tokens[0] if tokens else "")
        cat_name = doc.get("category_name", "")
        keywords = [k.strip() for k in cat_name.split(">") if k.strip()]
        description = doc.get("place_url", "")

        try:
            lat = float(doc.get("y", 0))
            lon = float(doc.get("x", 0))
        except (ValueError, TypeError):
            lat, lon = 0.0, 0.0

        return cls(
            name=raw_name,
            area=area,
            category=category,
            address=address,
            road_address=road_addr,
            latitude=lat,
            longitude=lon,
            search_rank=search_rank,
            keywords=keywords,
            main_description=description,
            brief_description=description[:60],
            link=doc.get("place_url", ""),
            telephone=doc.get("phone", ""),
        )
