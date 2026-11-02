import re

from ..checksum_utility import ChecksumUtility as chut


class ClRutDetector:
    """finds Chile RUT and RUN numbers in a cell, our stand-in for Macie's
    CHILE_RUT_NUMBER. Macie publishes the keywords and that numbers whose
    digits are all zeroes, e.g. 00000000-K, are never reported. The format
    is ours, from Chile's Servicio de Registro Civil: a 7 or 8 digit body,
    optionally with thousands dots (12.345.678), an optional hyphen, and a
    check character 0-9 or K (mod 11)."""

    CANDIDATES = re.compile(
        r"(?<![\w.])"
        r"(?:(?P<dotted>\d{1,2}\.\d{3}\.\d{3})|(?P<plain>\d{7,8}))"
        r"-?(?P<check>[0-9Kk])"
        r"(?![\w])",
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
            body = (m.group("dotted") or m.group("plain")).replace(".", "")
            if self.is_rut(body=body, check=m.group("check")):
                found.append((m.start(), m.end()))
        return found

    def is_rut(self, *, body: str, check: str) -> bool:
        if len(body) not in (7, 8) or set(body) == {"0"}:
            return False
        return chut.rut_check(body=body) == check.upper()
