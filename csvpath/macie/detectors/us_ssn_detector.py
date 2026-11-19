import re

from ..macie_exceptions import MacieException


class UsSsnDetector:
    """finds US Social Security numbers in a cell, our stand-in for Macie's
    USA_SOCIAL_SECURITY_NUMBER. Macie publishes only its keywords, so the
    format is the Social Security Administration's: area-group-serial,
    AAA-GG-SSSS, with no area 000, 666 or 900-999, no group 00 and no
    serial 0000. Hyphens only: the seventh live probe (2026-11-18) found
    no SSN with spaces or no separator, even after a keyword. Numbers in
    the catalog's exclusions are never reported."""

    CANDIDATES = re.compile(
        r"(?<!\d)(?P<a>\d{3})-(?P<g>\d{2})-(?P<n>\d{4})(?!\d)",
        re.ASCII,
    )

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = ("exclusions",)

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        exclusions = config.get("exclusions") or []
        if not isinstance(exclusions, list):
            raise MacieException("us_ssn exclusions must be a list")
        for e in exclusions:
            if not (isinstance(e, str) and len(e) == 9 and e.isdigit()):
                raise MacieException(f"us_ssn exclusion {e!r} must be 9 digits")
        self.exclusions = set(exclusions)

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        """the (start, end) of every SSN in the cell"""
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            if self.is_ssn(area=m.group("a"), group=m.group("g"), serial=m.group("n")):
                found.append((m.start(), m.end()))
        return found

    def is_ssn(self, *, area: str, group: str, serial: str) -> bool:
        if area == "000" or area == "666" or area.startswith("9"):
            return False
        if group == "00" or serial == "0000":
            return False
        return f"{area}{group}{serial}" not in self.exclusions
