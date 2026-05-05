from dataclasses import dataclass

from app.domains.home.domain.events.home_event import HomeEventType


@dataclass
class RecordHomeEventRequestDto:
    event_name: HomeEventType
    session_id: str
    timestamp: str
    page_path: str
