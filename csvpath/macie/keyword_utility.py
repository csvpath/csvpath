import re


class KeywordUtility:
    """Macie keyword matching.

    Keywords are case-insensitive. A keyword with spaces also matches with
    the spaces removed or replaced by "_" or "-", so "employee id" matches
    a header named employee_id. Macie documents that rule for managed data
    identifiers; we apply it to custom identifiers too (to confirm in the
    fidelity scan against real Macie).

    In-cell searches run on the original cell text with re.IGNORECASE, not
    on a lowercased copy: lowercasing can change a string's length (e.g.
    "İ"), which would misalign positions with the identifier's regex match.
    """

    @classmethod
    def variants(cls, *, keyword: str) -> set[str]:
        if not isinstance(keyword, str):
            raise TypeError(f"keyword must be a str, not {type(keyword)}")
        k = keyword.strip().lower()
        if k == "":
            raise ValueError("keyword cannot be empty")
        return {k, k.replace(" ", ""), k.replace(" ", "_"), k.replace(" ", "-")}

    @classmethod
    def all_variants(cls, *, keywords: list[str]) -> list[str]:
        if not isinstance(keywords, list):
            raise TypeError(f"keywords must be a list, not {type(keywords)}")
        found = set()
        for keyword in keywords:
            found |= cls.variants(keyword=keyword)
        #
        # sorted so results never depend on set order
        #
        return sorted(found)

    @classmethod
    def patterns(cls, *, variants: list[str]) -> list[re.Pattern]:
        """one lookahead pattern per variant, so that overlapping keyword
        occurrences are all found"""
        if not isinstance(variants, list):
            raise TypeError(f"variants must be a list, not {type(variants)}")
        return [re.compile(f"(?=({re.escape(v)}))", re.IGNORECASE) for v in variants]

    @classmethod
    def in_header(cls, *, header: str, variants: list[str]) -> bool:
        if not isinstance(header, str):
            raise TypeError(f"header must be a str, not {type(header)}")
        if not isinstance(variants, list):
            raise TypeError(f"variants must be a list, not {type(variants)}")
        h = header.lower()
        return any(v in h for v in variants)

    @classmethod
    def precedes(
        cls,
        *,
        cell: str,
        match_start: int,
        match_end: int,
        patterns: list[re.Pattern],
        distance: int,
    ) -> bool:
        """True if a complete keyword ends at or before match_start and the
        characters from the end of that keyword to the end of the match
        are at most distance."""
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        if not isinstance(patterns, list):
            raise TypeError(f"patterns must be a list, not {type(patterns)}")
        if not isinstance(distance, int) or isinstance(distance, bool) or distance < 1:
            raise ValueError(f"distance must be a positive int, not {distance!r}")
        if not 0 <= match_start <= match_end <= len(cell):
            raise ValueError(
                f"Bad match span {match_start}..{match_end} for a cell of length {len(cell)}"
            )
        for p in patterns:
            #
            # endpos keeps the keyword from running into the match. pos
            # skips keywords that can only end too far back; the keyword
            # text is at most a few characters longer than the pattern.
            #
            pos = max(0, match_end - distance - 2 * len(p.pattern))
            for m in p.finditer(cell, pos, match_start):
                if match_end - m.end(1) <= distance:
                    return True
        return False
