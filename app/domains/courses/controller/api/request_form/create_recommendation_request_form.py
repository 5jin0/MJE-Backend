from typing import Literal

from pydantic import BaseModel

from app.domains.courses.service.dto.request.create_recommendation_request_dto import (
    CreateRecommendationRequestDto,
)


class CreateRecommendationRequestForm(BaseModel):
    area: str
    start_time: str
    transport: Literal["walk", "public_transit", "car"]

    def to_request(self) -> CreateRecommendationRequestDto:
        return CreateRecommendationRequestDto(
            area=self.area,
            start_time=self.start_time,
            transport=self.transport,
        )
