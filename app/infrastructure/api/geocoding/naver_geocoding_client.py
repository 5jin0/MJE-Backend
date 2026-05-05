import logging
from typing import Optional, Tuple

import httpx

from app.domains.recommendation.service.geocoding_client_interface import GeocodingClientInterface

_GEOCODE_URL = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
_TIMEOUT_SECONDS = 3.0
_logger = logging.getLogger(__name__)


class NaverGeocodingClient(GeocodingClientInterface):
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def geocode(self, area: str) -> Optional[Tuple[float, float]]:
        try:
            response = httpx.get(
                _GEOCODE_URL,
                params={"query": area},
                headers={
                    "X-NCP-APIGW-API-KEY-ID": self._client_id,
                    "X-NCP-APIGW-API-KEY": self._client_secret,
                },
                timeout=_TIMEOUT_SECONDS,
            )
            if not response.is_success:
                _logger.error("[Geocoding] API error: area=%r status=%d", area, response.status_code)
                return None
            addresses = response.json().get("addresses", [])
            if not addresses:
                _logger.warning("[Geocoding] no result: area=%r", area)
                return None
            lon = float(addresses[0]["x"])
            lat = float(addresses[0]["y"])
            _logger.info("[Geocoding] area=%r -> (lon=%.6f, lat=%.6f)", area, lon, lat)
            return lon, lat
        except Exception as e:
            _logger.error("[Geocoding] error: area=%r error=%r", area, str(e))
            return None
