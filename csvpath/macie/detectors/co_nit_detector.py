import re

from ..util.checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class CoNitDetector:
    """finds Colombian NITs in a cell, our stand-in for Macie's
    COLOMBIA_INDIVIDUAL_NIT_NUMBER and COLOMBIA_ORGANIZATION_NIT_NUMBER.
    Macie publishes only the keywords, one list for both. The format is
    ours, from the DIAN: a body of digits and a check digit (chut.co_nit),
    printed with thousands dots and a hyphen before the check digit
    (900.123.456-7), plain with the hyphen (900123456-7), or contiguous
    (9001234567, the check digit last).

    Nothing in a NIT says whether it is a person's or an organization's.
    Ours (David, 2026-11-03): a body of 9 digits starting 8 or 9 is an
    organization's, the usual rule for personas juridicas; any other body
    of 6 to 10 digits, e.g. a cedula, is a person's. All zeroes is never
    reported. NITs must not touch other digits. The catalog detector's
    data gives the form:

        form    "individual" or "organization"
    """

    FORMS = ("individual", "organization")
    CANDIDATES = re.compile(
        r"(?<![0-9.,])(?:"
        r"(?P<body>\d{1,3}(?:\.\d{3}){1,3}|\d{6,10})[- ](?P<check>\d)"
        r"|(?P<run>\d{7,11})"
        r")(?![0-9])",
        re.ASCII,
    )

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.form = config.get("form")
        if self.form not in self.FORMS:
            raise MacieException(
                f"form must be one of {list(self.FORMS)}, not {self.form!r}"
            )

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            if m.group("run") is not None:
                body, check = m.group("run")[:-1], m.group("run")[-1]
            else:
                body, check = m.group("body").replace(".", ""), m.group("check")
            if self.is_nit(body=body, check=check):
                found.append((m.start(), m.end()))
        return found

    def is_nit(self, *, body: str, check: str) -> bool:
        if not 6 <= len(body) <= 10 or set(body) == {"0"}:
            return False
        organization = len(body) == 9 and body[0] in "89"
        if organization != (self.form == "organization"):
            return False
        return chut.co_nit(digits=body + check)
