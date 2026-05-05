from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class ImageResult:
    title: str
    link: str
    thumbnail: str


class ImageSearchClientInterface(ABC):
    @abstractmethod
    def search(self, query: str) -> List[ImageResult]: ...
