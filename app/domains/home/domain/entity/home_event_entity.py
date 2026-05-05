from dataclasses import dataclass
from typing import Optional

from app.domains.home.domain.events.home_event import HomeEventType


@dataclass
class HomeEventEntity:
    event_name: HomeEventType
    session_id: str
    timestamp: str
    page_path: str
    id: Optional[int] = None
