from typing import List

import httpx

from app.domains.recommendation.service.datalab_client_interface import (
    DataLabClientInterface,
    DataLabDataPoint,
    DataLabRequest,
    DataLabResponse,
    DataLabResultItem,
)

_DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"
_TIMEOUT_SECONDS = 5.0


class NaverDataLabClient(DataLabClientInterface):
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def fetch(self, request: DataLabRequest) -> DataLabResponse:
        body = {
            "startDate": request.start_date,
            "endDate": request.end_date,
            "timeUnit": request.time_unit,
            "keywordGroups": [
                {"groupName": g.group_name, "keywords": g.keywords}
                for g in request.keyword_groups
            ],
        }
        response = httpx.post(
            _DATALAB_URL,
            json=body,
            headers={
                "X-Naver-Client-Id": self._client_id,
                "X-Naver-Client-Secret": self._client_secret,
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return self._parse(response.json())

    def _parse(self, data: dict) -> DataLabResponse:
        results: List[DataLabResultItem] = []
        for item in data.get("results", []):
            data_points = [
                DataLabDataPoint(period=d["period"], ratio=float(d["ratio"]))
                for d in item.get("data", [])
            ]
            results.append(DataLabResultItem(
                title=item["title"],
                keywords=item.get("keywords", []),
                data=data_points,
            ))
        return DataLabResponse(results=results)
