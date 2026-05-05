from typing import List, Optional, Tuple


class ImageRelevanceService:
    def validate_image(
        self,
        image_title: str,
        image_link: str,
        place_name: str,
        area: str,
        category: str,
        keyword: str,
    ) -> bool:
        keywords = self._extract_keywords(place_name, area, category, keyword)
        text = (image_title + " " + image_link).lower()
        return any(kw.lower() in text for kw in keywords)

    def select_representative_image(
        self,
        candidates: List[Tuple[str, str, str, str]],
        course_keywords: List[str],
    ) -> Optional[str]:
        """
        candidates: [(image_url, place_name, category, keyword), ...]
        course_keywords: keywords for relevance scoring
        Returns the most relevant non-empty image_url, or None.
        """
        best_url: Optional[str] = None
        best_score = -1

        for url, name, category, keyword in candidates:
            if not url:
                continue
            score = self._relevance_score(url, name, category, keyword, course_keywords)
            if score > best_score:
                best_score = score
                best_url = url

        return best_url

    def _relevance_score(
        self,
        url: str,
        name: str,
        category: str,
        keyword: str,
        course_keywords: List[str],
    ) -> float:
        if not course_keywords:
            return 0.0
        text = " ".join([url, name, category, keyword]).lower()
        matches = sum(1 for kw in course_keywords if kw.lower() in text)
        return matches / len(course_keywords)

    def _extract_keywords(self, *texts: str) -> List[str]:
        keywords = []
        for text in texts:
            keywords.extend(w for w in text.split() if len(w) > 1)
        return list(set(keywords))
