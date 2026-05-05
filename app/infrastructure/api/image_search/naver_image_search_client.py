from typing import List

import httpx

from app.domains.recommendation.service.image_search_client_interface import (
    ImageResult,
    ImageSearchClientInterface,
)

_NAVER_IMAGE_SEARCH_URL = "https://openapi.naver.com/v1/search/image"
_DISPLAY_COUNT = 5
_TIMEOUT_SECONDS = 3.0


class NaverImageSearchClient(ImageSearchClientInterface):
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def search(self, query: str) -> List[ImageResult]:
        try:
            response = httpx.get(
                _NAVER_IMAGE_SEARCH_URL,
                params={"query": query, "display": _DISPLAY_COUNT, "sort": "sim"},
                headers={
                    "X-Naver-Client-Id": self._client_id,
                    "X-Naver-Client-Secret": self._client_secret,
                },
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            return [
                ImageResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    thumbnail=item.get("thumbnail", ""),
                )
                for item in items
            ]
        except Exception:
            return []
