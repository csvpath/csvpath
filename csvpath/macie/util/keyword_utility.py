import re
import unicodedata


class KeywordUtility:
    """Macie keyword matching.

    Keywords are case-insensitive. A keyword with spaces also matches with
    the spaces removed or replaced by "_" or "-", so "employee id" matches
    a header named employee_id. Macie documents that rule for managed data
    identifiers; the live check (2026-11-11) confirmed it for custom
    identifiers too.

    Keywords match as whole words, not substrings: a keyword that starts
    or ends with a letter or digit does not count where a letter or digit
    touches it. "ssn" is a keyword in customer_ssn and "ssn: ..." but not
    in ssnumber or myssn. "_", "-", spaces and punctuation separate words.
    Confirmed for managed identifiers by the third live probe
    (2026-11-15); applied to custom identifiers too, as one rule.

    Keywords match without their accents: cédula de ciudadanía matches
    "cedula de ciudadania", and the other way round (the seventh live
    probe, 2026-11-18). Keywords and the text searched are folded one
    character at a time, each to its base letter, so the folded text keeps
    the original's positions.

    A keyword in a cell counts only before the occurrence, not after it
    (the seventh live probe).

    In-cell searches run on the folded cell text with re.IGNORECASE, not
    on a lowercased copy: lowercasing can change a string's length (e.g.
    "İ"), which would misalign positions with the identifier's regex match.
    """

    @classmethod
    def fold(cls, *, text: str) -> str:
        """each character to its base letter, without accents: "é" to "e",
        "ç" to "c". One character for one, so positions do not move; a
        character with no base letter (ß, ł) stays as it is"""
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        return "".join(cls._fold_char(c) for c in text)

    @classmethod
    def _fold_char(cls, c: str) -> str:
        if c.isascii():
            return c
        base = unicodedata.normalize("NFD", c)[0]
        return base if len(base) == 1 else c

    @classmethod
    def variants(cls, *, keyword: str) -> set[str]:
        if not isinstance(keyword, str):
            raise TypeError(f"keyword must be a str, not {type(keyword)}")
        k = cls.fold(text=keyword.strip().lower())
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
        h = cls.fold(text=header.lower())
        for v in variants:
            start = h.find(v)
            while start != -1:
                if cls.is_word(text=h, start=start, end=start + len(v)):
                    return True
                start = h.find(v, start + 1)
        return False

    @classmethod
    def is_word(cls, *, text: str, start: int, end: int) -> bool:
        """True if text[start:end] is not touched by a letter or digit at
        an edge where it has one itself. "dl#" ends in "#", so "dl#123"
        still holds the keyword."""
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        if not 0 <= start < end <= len(text):
            raise ValueError(
                f"Bad span {start}..{end} for a text of length {len(text)}"
            )
        if text[start].isalnum() and start > 0 and text[start - 1].isalnum():
            return False
        if text[end - 1].isalnum() and end < len(text) and text[end].isalnum():
            return False
        return True

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
        folded = cls.fold(text=cell)
        for p in patterns:
            #
            # endpos keeps the keyword from running into the match. pos
            # skips keywords that can only end too far back; the keyword
            # text is at most a few characters longer than the pattern.
            #
            pos = max(0, match_end - distance - 2 * len(p.pattern))
            for m in p.finditer(folded, pos, match_start):
                if match_end - m.end(1) <= distance and cls.is_word(
                    text=folded, start=m.start(1), end=m.end(1)
                ):
                    return True
        return False

    @classmethod
    def near(
        cls,
        *,
        cell: str,
        match_start: int,
        match_end: int,
        patterns: list[re.Pattern],
        distance: int,
    ) -> bool:
        """the managed identifier rule: True if a complete keyword is before
        the match, not overlapping it, with at most distance characters
        between them. Macie: "in proximity", "typically within 30
        characters (inclusively)". Before only: the seventh live probe
        (2026-11-18) found no SSN with its keyword after it"""
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
        folded = cls.fold(text=cell)
        for p in patterns:
            #
            # the keyword ends at or before match_start. endpos keeps it from
            # running into the match
            #
            pos = max(0, match_start - distance - 2 * len(p.pattern))
            for m in p.finditer(folded, pos, match_start):
                if match_start - m.end(1) <= distance and cls.is_word(
                    text=folded, start=m.start(1), end=m.end(1)
                ):
                    return True
        return False
