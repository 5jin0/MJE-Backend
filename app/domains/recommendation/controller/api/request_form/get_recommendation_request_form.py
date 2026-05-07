from typing import Literal, Optional

from pydantic import BaseModel

from app.domains.recommendation.service.dto.request.get_recommendation_request_dto import (
    GetRecommendationRequestDto,
)


class GetRecommendationRequestForm(BaseModel):
    area: str
    start_time: str
    transport: Literal["walk", "public_transit", "car"]
    seed: Optional[int] = None

    def to_request(self) -> GetRecommendationRequestDto:
        return GetRecommendationRequestDto(
            area=self.area,
            start_time=self.start_time,
            transport=self.transport,
            seed=self.seed,
        )
