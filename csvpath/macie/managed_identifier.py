from .allow_list_set import AllowListSet
from .detectors import DETECTORS
from .keyword_utility import KeywordUtility as keut
from .macie_exceptions import MacieException
from .managed_catalog import ManagedCatalog
from .severity_levels import SeverityLevels


class ManagedIdentifier:
    """one Macie managed data identifier, as our stand-in: a detector finds
    candidates in a cell, then the keyword rule and the allow lists decide
    which are occurrences. Returns counts only, never matched values.

    keyword_mode:
      required  a keyword in the column name, or near the occurrence in the
                cell (before or after, within distance)
      absent    reported only when there is no keyword there, e.g.
                CREDIT_CARD_NUMBER_(NO_KEYWORD)
      none      keywords are not considered"""

    def __init__(
        self,
        *,
        name: str,
        category: str,
        detector: str,
        keyword_mode: str,
        keywords: list[str],
        distance: int,
        severity: SeverityLevels,
        catalog: ManagedCatalog,
    ) -> None:
        for n, v in [("name", name), ("category", category), ("detector", detector)]:
            if not isinstance(v, str) or v.strip() == "":
                raise ValueError(f"{n} must be a non-empty str")
        if keyword_mode not in ManagedCatalog.KEYWORD_MODES:
            raise MacieException(
                f"keyword_mode must be one of {ManagedCatalog.KEYWORD_MODES}, "
                f"not {keyword_mode!r}"
            )
        if not isinstance(keywords, list):
            raise TypeError(f"keywords must be a list, not {type(keywords)}")
        if keyword_mode != "none" and len(keywords) == 0:
            raise MacieException(
                f"{name} has keyword_mode {keyword_mode} but no keywords"
            )
        if (
            not isinstance(distance, int)
            or isinstance(distance, bool)
            or not 1 <= distance <= 300
        ):
            raise ValueError(f"distance must be an int from 1 to 300, not {distance!r}")
        if not isinstance(severity, SeverityLevels):
            raise TypeError(f"severity must be SeverityLevels, not {type(severity)}")
        if not isinstance(catalog, ManagedCatalog):
            raise TypeError(f"catalog must be a ManagedCatalog, not {type(catalog)}")
        if detector not in DETECTORS:
            raise MacieException(f"No detector named {detector!r} for {name}")
        self.name = name
        self.category = category
        self.detector_name = detector
        self.detector = DETECTORS[detector](config=catalog.detector(name=detector))
        self.keyword_mode = keyword_mode
        self.keywords = keywords
        self.variants = keut.all_variants(keywords=keywords)
        self.keyword_patterns = keut.patterns(variants=self.variants)
        self.distance = distance
        self.severity = severity
        self._header_cache = {}

    def occurrences(self, *, cell: str, header: str, allow_lists: AllowListSet) -> int:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        if not isinstance(allow_lists, AllowListSet):
            raise TypeError(
                f"allow_lists must be an AllowListSet, not {type(allow_lists)}"
            )
        if cell == "":
            return 0
        count = 0
        for start, end in self.detector.matches(cell=cell):
            if not self._keyword_rule_passes(
                cell=cell, header=header, start=start, end=end
            ):
                continue
            if allow_lists.allows(text=cell[start:end]):
                continue
            count += 1
        return count

    def _keyword_rule_passes(
        self, *, cell: str, header: str, start: int, end: int
    ) -> bool:
        if self.keyword_mode == "none":
            return True
        found = self._keyword_in_header(header=header) or keut.near(
            cell=cell,
            match_start=start,
            match_end=end,
            patterns=self.keyword_patterns,
            distance=self.distance,
        )
        if self.keyword_mode == "required":
            return found
        return not found

    def _keyword_in_header(self, *, header: str) -> bool:
        if header not in self._header_cache:
            self._header_cache[header] = keut.in_header(
                header=header, variants=self.variants
            )
        return self._header_cache[header]
