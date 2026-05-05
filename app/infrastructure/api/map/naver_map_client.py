from typing import Optional, Tuple

import httpx

from app.domains.recommendation.domain.value_object.transport import Transport
from app.domains.recommendation.service.map_client_interface import (
    MapClientInterface,
    RouteInfo,
    RouteRequest,
)

_WALKING_URL = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/walking"
_DRIVING_URL = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving"
_TIMEOUT_SECONDS = 5.0
_MS_PER_MINUTE = 60_000

_FALLBACK_MINUTES = {
    Transport.WALK: 15,
    Transport.PUBLIC_TRANSIT: 25,
    Transport.CAR: 30,
}

_KR_LON_RANGE = (124.0, 132.0)
_KR_LAT_RANGE = (33.0, 39.0)


def _parse_wgs84(mapx: str, mapy: str) -> Optional[Tuple[float, float]]:
    try:
        x, y = float(mapx), float(mapy)
        for factor in (1, 10_000, 10_000_000):
            lx, ly = x / factor, y / factor
            if _KR_LON_RANGE[0] <= lx <= _KR_LON_RANGE[1] and _KR_LAT_RANGE[0] <= ly <= _KR_LAT_RANGE[1]:
                return lx, ly
        return None
    except (ValueError, ZeroDivisionError):
        return None


class NaverMapClient(MapClientInterface):
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def get_route(self, request: RouteRequest) -> RouteInfo:
        from_coords = _parse_wgs84(request.from_mapx, request.from_mapy)
        to_coords = _parse_wgs84(request.to_mapx, request.to_mapy)

        if from_coords is None or to_coords is None:
            return self._fallback(request)

        try:
            if request.transport == Transport.WALK:
                return self._fetch_walking(request, from_coords, to_coords)
            if request.transport == Transport.CAR:
                return self._fetch_driving(request, from_coords, to_coords)
            return self._fallback(request)
        except Exception:
            return self._fallback(request)

    def _fetch_walking(
        self,
        request: RouteRequest,
        from_coords: Tuple[float, float],
        to_coords: Tuple[float, float],
    ) -> RouteInfo:
        response = httpx.get(
            _WALKING_URL,
            params={
                "start": f"{from_coords[0]},{from_coords[1]}",
                "goal": f"{to_coords[0]},{to_coords[1]}",
            },
            headers=self._headers(),
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        summary = data["route"]["pedestrian"][0]["summary"]
        return RouteInfo(
            from_mapx=request.from_mapx,
            from_mapy=request.from_mapy,
            to_mapx=request.to_mapx,
            to_mapy=request.to_mapy,
            transport=request.transport,
            duration_minutes=max(1, round(summary["duration"] / _MS_PER_MINUTE)),
            distance_meters=summary.get("distance", 0),
            is_fallback=False,
        )

    def _fetch_driving(
        self,
        request: RouteRequest,
        from_coords: Tuple[float, float],
        to_coords: Tuple[float, float],
    ) -> RouteInfo:
        response = httpx.get(
            _DRIVING_URL,
            params={
                "start": f"{from_coords[0]},{from_coords[1]}",
                "goal": f"{to_coords[0]},{to_coords[1]}",
                "option": "trafast",
            },
            headers=self._headers(),
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        summary = data["route"]["trafast"][0]["summary"]
        return RouteInfo(
            from_mapx=request.from_mapx,
            from_mapy=request.from_mapy,
            to_mapx=request.to_mapx,
            to_mapy=request.to_mapy,
            transport=request.transport,
            duration_minutes=max(1, round(summary["duration"] / _MS_PER_MINUTE)),
            distance_meters=summary.get("distance", 0),
            is_fallback=False,
        )

    def _fallback(self, request: RouteRequest) -> RouteInfo:
        return RouteInfo(
            from_mapx=request.from_mapx,
            from_mapy=request.from_mapy,
            to_mapx=request.to_mapx,
            to_mapy=request.to_mapy,
            transport=request.transport,
            duration_minutes=_FALLBACK_MINUTES[request.transport],
            distance_meters=0,
            is_fallback=True,
        )

    def _headers(self) -> dict:
        return {
            "X-NCP-APIGW-API-KEY-ID": self._client_id,
            "X-NCP-APIGW-API-KEY": self._client_secret,
        }
