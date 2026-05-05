import logging
from typing import List

import httpx

from app.domains.recommendation.service.search_client_interface import (
    RawPlaceResult,
    SearchClientInterface,
)

_LOCAL_SEARCH_URL = "https://openapi.naver.com/v1/search/local.json"
_TIMEOUT_SECONDS = 3.0
_logger = logging.getLogger(__name__)


class NaverSearchClient(SearchClientInterface):
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        if not client_id or not client_secret:
            _logger.warning(
                "NaverSearchClient initialized with empty credentials — all searches will fail with 401"
            )

    def search_places(self, query: str, display: int = 5) -> List[RawPlaceResult]:
        _logger.info("[Naver] search: query=%r display=%d", query, display)
        try:
            response = httpx.get(
                _LOCAL_SEARCH_URL,
                params={"query": query, "display": display, "sort": "comment"},
                headers={
                    "X-Naver-Client-Id": self._client_id,
                    "X-Naver-Client-Secret": self._client_secret,
                },
                timeout=_TIMEOUT_SECONDS,
            )
            _logger.info("[Naver] response: query=%r status=%d", query, response.status_code)
            if not response.is_success:
                _logger.error(
                    "[Naver] API error: query=%r status=%d body=%s",
                    query,
                    response.status_code,
                    response.text[:500],
                )
                return []
            response.raise_for_status()
            items = response.json().get("items", [])
            _logger.info("[Naver] result: query=%r items=%d", query, len(items))
            return [
                RawPlaceResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    category=item.get("category", ""),
                    description=item.get("description", ""),
                    telephone=item.get("telephone", ""),
                    address=item.get("address", ""),
                    road_address=item.get("roadAddress", ""),
                    mapx=item.get("mapx", ""),
                    mapy=item.get("mapy", ""),
                )
                for item in items
            ]
        except httpx.TimeoutException:
            _logger.error("[Naver] timeout: query=%r (limit=%.1fs)", query, _TIMEOUT_SECONDS)
            return []
        except httpx.ConnectError as e:
            _logger.error("[Naver] connect error: query=%r error=%r", query, str(e))
            return []
        except Exception as e:
            _logger.error("[Naver] unexpected error: query=%r type=%s error=%r", query, type(e).__name__, str(e))
            return []
