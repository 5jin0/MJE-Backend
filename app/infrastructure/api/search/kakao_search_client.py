import logging
from typing import List

import httpx

from app.domains.recommendation.service.search_client_interface import (
    RawPlaceResult,
    SearchClientInterface,
)

_KEYWORD_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
_TIMEOUT_SECONDS = 3.0
_logger = logging.getLogger(__name__)


class KakaoSearchClient(SearchClientInterface):
    def __init__(self, rest_api_key: str) -> None:
        self._rest_api_key = rest_api_key
        if not rest_api_key:
            _logger.warning(
                "KakaoSearchClient initialized with empty key — all searches will fail with 401"
            )

    def search_places(self, query: str, display: int = 5) -> List[RawPlaceResult]:
        _logger.info("[Kakao] search: query=%r display=%d", query, display)
        try:
            response = httpx.get(
                _KEYWORD_SEARCH_URL,
                params={"query": query, "size": min(display, 15)},
                headers={"Authorization": f"KakaoAK {self._rest_api_key}"},
                timeout=_TIMEOUT_SECONDS,
            )
            _logger.info("[Kakao] response: query=%r status=%d", query, response.status_code)
            if not response.is_success:
                _logger.error(
                    "[Kakao] API error: query=%r status=%d body=%s",
                    query,
                    response.status_code,
                    response.text[:500],
                )
                return []
            documents = response.json().get("documents", [])
            _logger.info("[Kakao] result: query=%r items=%d", query, len(documents))
            return [
                RawPlaceResult(
                    title=doc.get("place_name", ""),
                    link=doc.get("place_url", ""),
                    category=doc.get("category_name", ""),
                    description="",
                    telephone=doc.get("phone", ""),
                    address=doc.get("address_name", ""),
                    road_address=doc.get("road_address_name", ""),
                    mapx=doc.get("x", ""),
                    mapy=doc.get("y", ""),
                )
                for doc in documents
            ]
        except httpx.TimeoutException:
            _logger.error("[Kakao] timeout: query=%r (limit=%.1fs)", query, _TIMEOUT_SECONDS)
            return []
        except httpx.ConnectError as e:
            _logger.error("[Kakao] connect error: query=%r error=%r", query, str(e))
            return []
        except Exception as e:
            _logger.error("[Kakao] unexpected error: query=%r type=%s error=%r", query, type(e).__name__, str(e))
            return []
