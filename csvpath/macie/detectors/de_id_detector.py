import re

from ..util.checksum_utility import ChecksumUtility as chut


class DeIdDetector:
    """finds German identity card (Personalausweis) numbers in a cell, our
    stand-in for Macie's GERMANY_NATIONAL_IDENTIFICATION_NUMBER. Macie
    publishes only the keywords. The format is ours, from the
    Bundesministerium des Innern: 9 characters of 0-9 and the consonants
    C F G H J K L M N P R T V W X Y Z (no vowels, and not B D Q S), then an
    ICAO 9303 check digit (chut.icao_check): T220001293, the official
    specimen. Older, all digit numbers fit the same pattern. Letters may be
    upper or lower case; numbers must not touch other letters or digits."""

    CANDIDATES = re.compile(
        r"(?<![A-Za-z0-9])(?P<number>[0-9CFGHJ-NPRTV-Zcfghj-nprtv-z]{9})(?P<check>\d)(?![A-Za-z0-9])",
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
            #
            # an all digit number passes the check one time in ten, so
            # near a broad keyword such as "id number" this over-reports;
            # the keyword is still required
            #
            if chut.icao_check(text=m.group("number")) == m.group("check"):
                found.append((m.start(), m.end()))
        return found
