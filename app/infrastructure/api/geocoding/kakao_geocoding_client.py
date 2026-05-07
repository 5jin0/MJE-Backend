import logging
from typing import Optional, Tuple

import httpx

from app.domains.recommendation.service.geocoding_client_interface import GeocodingClientInterface

_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"
_TIMEOUT_SECONDS = 3.0
_logger = logging.getLogger(__name__)


class KakaoGeocodingClient(GeocodingClientInterface):
    def __init__(self, rest_api_key: str) -> None:
        self._rest_api_key = rest_api_key

    def geocode(self, area: str) -> Optional[Tuple[float, float]]:
        try:
            response = httpx.get(
                _GEOCODE_URL,
                params={"query": area},
                headers={"Authorization": f"KakaoAK {self._rest_api_key}"},
                timeout=_TIMEOUT_SECONDS,
            )
            if not response.is_success:
                _logger.error("[Geocoding] API error: area=%r status=%d", area, response.status_code)
                return None
            documents = response.json().get("documents", [])
            if not documents:
                _logger.warning("[Geocoding] no result: area=%r", area)
                return None
            lon = float(documents[0]["x"])
            lat = float(documents[0]["y"])
            _logger.info("[Geocoding] area=%r -> (lon=%.6f, lat=%.6f)", area, lon, lat)
            return lon, lat
        except Exception as e:
            _logger.error("[Geocoding] error: area=%r error=%r", area, str(e))
            return None
