from dataclasses import dataclass


@dataclass
class CreateRecommendationRequestDto:
    area: str
    start_time: str
    transport: str
