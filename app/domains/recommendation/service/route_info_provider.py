from typing import List

from app.domains.recommendation.domain.value_object.candidate_place import CandidatePlace
from app.domains.recommendation.domain.value_object.transport import Transport
from app.domains.recommendation.service.map_client_interface import (
    MapClientInterface,
    RouteInfo,
    RouteRequest,
)


class RouteInfoProvider:
    def __init__(self, client: MapClientInterface) -> None:
        self._client = client

    def get_routes_for_course(
        self,
        places: List[CandidatePlace],
        transport: Transport,
    ) -> List[RouteInfo]:
        routes: List[RouteInfo] = []
        for i in range(len(places) - 1):
            from_place = places[i]
            to_place = places[i + 1]
            request = RouteRequest(
                from_mapx=from_place.mapx,
                from_mapy=from_place.mapy,
                to_mapx=to_place.mapx,
                to_mapy=to_place.mapy,
                transport=transport,
            )
            routes.append(self._client.get_route(request))
        return routes
