import re

from ..checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class UsNpiDetector:
    """finds US National Provider Identifiers in a cell, our stand-in for
    Macie's USA_NATIONAL_PROVIDER_IDENTIFIER. Macie publishes only its
    keywords, so the format is CMS's: 10 digits, starting with 1 or 2,
    whose check digit is the Luhn check digit of the number prefixed with
    the health industry card issuer prefix 80840. Numbers in the catalog's
    exclusions are never reported."""

    CANDIDATES = re.compile(r"(?<!\d)[12]\d{9}(?!\d)", re.ASCII)
    PREFIX = "80840"

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        exclusions = config.get("exclusions") or []
        if not isinstance(exclusions, list):
            raise MacieException("us_npi exclusions must be a list")
        for e in exclusions:
            if not (isinstance(e, str) and len(e) == 10 and e.isdigit()):
                raise MacieException(f"us_npi exclusion {e!r} must be 10 digits")
        self.exclusions = set(exclusions)

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        """the (start, end) of every NPI in the cell"""
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            if self.is_npi(digits=m.group(0)):
                found.append((m.start(), m.end()))
        return found

    def is_npi(self, *, digits: str) -> bool:
        if digits in self.exclusions:
            return False
        return chut.luhn(digits=f"{self.PREFIX}{digits}")
