from .allow_list_set import AllowListSet
from .keyword_utility import KeywordUtility as keut
from .regex_utility import RegexUtility as reut
from .severity_levels import SeverityLevels


class CustomIdentifier:
    """one Macie custom data identifier, ready to check cells.

    For each non-overlapping regex match in a cell, in order, a match is an
    occurrence only if:

    1. the identifier has no keywords, or a keyword is in the column
       header, or a keyword ends before the match within `distance`
       characters of the match end;
    2. the matched text contains no ignore word (case-sensitive);
    3. no allow list allows the matched text.

    Only counts come out. Matched values are never kept.
    """

    DEFAULT_DISTANCE = 50

    def __init__(
        self,
        *,
        name: str,
        pattern: str,
        keywords: list[str],
        ignore_words: list[str],
        distance: int,
        severity: SeverityLevels,
    ) -> None:
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("name must be a non-empty str")
        if not isinstance(keywords, list) or not isinstance(ignore_words, list):
            raise TypeError("keywords and ignore_words must be lists")
        if (
            not isinstance(distance, int)
            or isinstance(distance, bool)
            or not 1 <= distance <= 300
        ):
            raise ValueError(f"distance must be an int from 1 to 300, not {distance!r}")
        if not isinstance(severity, SeverityLevels):
            raise TypeError(f"severity must be SeverityLevels, not {type(severity)}")
        for w in ignore_words:
            if not isinstance(w, str) or w == "":
                raise ValueError(f"Bad ignore word {w!r} in {name}")
        self.name = name
        self.pattern = pattern
        self.regex = reut.compile(pattern=pattern)
        self.keywords = keywords
        self.variants = keut.all_variants(keywords=keywords)
        self.keyword_patterns = keut.patterns(variants=self.variants)
        self.ignore_words = ignore_words
        self.distance = distance
        self.severity = severity
        #
        # header -> keyword in header? headers repeat on every line
        #
        self._header_cache = {}

    @classmethod
    def from_aws(cls, *, cdi: dict) -> "CustomIdentifier":
        """from a verbatim GetCustomDataIdentifier response"""
        if not isinstance(cdi, dict):
            raise TypeError(f"cdi must be a dict, not {type(cdi)}")
        distance = cdi.get("maximumMatchDistance")
        return cls(
            name=cdi["name"],
            pattern=cdi["regex"],
            keywords=cdi.get("keywords") or [],
            ignore_words=cdi.get("ignoreWords") or [],
            distance=cls.DEFAULT_DISTANCE if distance is None else distance,
            severity=SeverityLevels.from_aws(severity_levels=cdi.get("severityLevels")),
        )

    def occurrences(self, *, cell: str, header: str, allow_lists: AllowListSet) -> int:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        if not isinstance(allow_lists, AllowListSet):
            raise TypeError(
                f"allow_lists must be an AllowListSet, not {type(allow_lists)}"
            )
        if cell == "":
            return 0
        header_ok = self._keyword_in_header(header=header)
        count = 0
        for m in self.regex.finditer(cell):
            if not header_ok and not keut.precedes(
                cell=cell,
                match_start=m.start(),
                match_end=m.end(),
                patterns=self.keyword_patterns,
                distance=self.distance,
            ):
                continue
            text = m.group(0)
            if any(w in text for w in self.ignore_words):
                continue
            if allow_lists.allows(text=text):
                continue
            count += 1
        return count

    def _keyword_in_header(self, *, header: str) -> bool:
        if not self.keywords:
            return True
        if header not in self._header_cache:
            self._header_cache[header] = keut.in_header(
                header=header, variants=self.variants
            )
        return self._header_cache[header]
