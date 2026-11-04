import re

from ..checksum_utility import ChecksumUtility as chut


class FrNirDetector:
    """finds French NIR (INSEE, social security) numbers in a cell, our
    stand-in for Macie's FRANCE_NATIONAL_IDENTIFICATION_NUMBER. Macie
    publishes only the keywords. The format is ours, from INSEE: 15
    characters, a sex digit, year, month, a department of 2 digits or 2A or
    2B (Corsica), 3 digits for the commune, 3 for the order, then a 2 digit
    key (chut.fr_nir_key). Printed contiguous, as 1 2 2 2 3 3 2 separated
    by spaces or dots, one separator throughout, or with only the key
    apart: 1850578006084 36.

    Ours: no rule on the sex digit or the month. INSEE uses values beyond
    1-2 and 01-12 for some people, and a rule we cannot confirm would miss
    real numbers. Numbers must not touch other letters or digits."""

    DEPARTMENT = r"(?:\d{2}|2[ABab])"
    CANDIDATES = re.compile(
        r"(?<![A-Za-z0-9.])(?:"
        rf"\d(?P<s>[ .])\d{{2}}(?P=s)\d{{2}}(?P=s){DEPARTMENT}(?P=s)\d{{3}}(?P=s)\d{{3}}(?P=s)\d{{2}}"
        rf"|\d{{5}}{DEPARTMENT}\d{{6}} ?\d{{2}}"
        r")(?![A-Za-z0-9])",
        re.ASCII,
    )

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            nir = re.sub(r"[ .]", "", m.group(0))
            if chut.fr_nir_key(nir=nir):
                found.append((m.start(), m.end()))
        return found
