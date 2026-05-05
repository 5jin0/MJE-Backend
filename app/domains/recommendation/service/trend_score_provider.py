from datetime import datetime, timedelta
from typing import Dict, List

from app.domains.recommendation.service.datalab_client_interface import (
    DataLabClientInterface,
    DataLabDataPoint,
    DataLabRequest,
)
from app.domains.recommendation.service.keyword_group_builder import KeywordGroupBuilder

_BATCH_SIZE = 5
_TIME_UNIT = "month"
_LOOKBACK_DAYS = 90
_FALLBACK_SCORE = 50.0


class TrendScoreProvider:
    def __init__(self, client: DataLabClientInterface) -> None:
        self._client = client
        self._builder = KeywordGroupBuilder()

    def get_trend_scores(self, area: str) -> Dict[str, float]:
        all_groups = self._builder.build_for_area(area)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

        scores: Dict[str, float] = {}

        for i in range(0, len(all_groups), _BATCH_SIZE):
            batch = all_groups[i : i + _BATCH_SIZE]
            request = DataLabRequest(
                start_date=start_date,
                end_date=end_date,
                time_unit=_TIME_UNIT,
                keyword_groups=batch,
            )
            try:
                response = self._client.fetch(request)
                for result in response.results:
                    scores[result.title] = self._normalize(result.data)
            except Exception:
                for group in batch:
                    scores.setdefault(group.group_name, _FALLBACK_SCORE)

        for group in all_groups:
            scores.setdefault(group.group_name, _FALLBACK_SCORE)

        return scores

    def _normalize(self, data: List[DataLabDataPoint]) -> float:
        if not data:
            return _FALLBACK_SCORE
        avg_ratio = sum(d.ratio for d in data) / len(data)
        return round(min(100.0, max(0.0, avg_ratio)), 2)
