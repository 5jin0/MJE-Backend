from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GetRecommendationRequestDto:
    area: str
    start_time: str
    transport: str
    seed: Optional[int] = field(default=None)
