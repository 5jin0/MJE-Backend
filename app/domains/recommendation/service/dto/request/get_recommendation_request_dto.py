from dataclasses import dataclass


@dataclass
class GetRecommendationRequestDto:
    area: str
    start_time: str
    transport: str
