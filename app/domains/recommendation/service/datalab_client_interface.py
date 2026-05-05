from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class DataLabKeywordGroup:
    group_name: str
    keywords: List[str]


@dataclass
class DataLabDataPoint:
    period: str
    ratio: float


@dataclass
class DataLabResultItem:
    title: str
    keywords: List[str]
    data: List[DataLabDataPoint]


@dataclass
class DataLabRequest:
    start_date: str
    end_date: str
    time_unit: str
    keyword_groups: List[DataLabKeywordGroup]


@dataclass
class DataLabResponse:
    results: List[DataLabResultItem] = field(default_factory=list)


class DataLabClientInterface(ABC):
    @abstractmethod
    def fetch(self, request: DataLabRequest) -> DataLabResponse: ...
