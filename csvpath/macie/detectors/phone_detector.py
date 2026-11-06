import re

from ..macie_exceptions import MacieException
from .format_detector import FormatDetector


class PhoneDetector:
    """finds one country's phone numbers in a cell, our stand-in for
    Macie's phone number identifiers. Macie: a number near a keyword need
    not include a country code; a number with no keyword near must include
    one. So a number written with its country code (+44 or 0044) is
    keyword exempt, through the same keyword_exempt hook as the bank
    detector's IBANs, and every other number needs a keyword.

    The catalog detector's data is the country's numbering plan, ours, from
    the national regulators (checked against Google's phonenumbers library
    in the tests):

        country_code     e.g. "44"
        trunk            the national trunk prefix, e.g. "0", or ""
        trunk_required   true if a national number must start with the
                         trunk (UK, France, Germany); false if it may be
                         left off (US 1, Brazil 0)
        nsn_formats      the national significant number, without the
                         trunk or separators, in FormatDetector's notation,
                         e.g. "[2-9]##[2-9]######" for the US

    A number is digits with spaces, dots, hyphens or parentheses between
    them, after an optional + or 00 and the country code. An international
    number may keep the trunk in parentheses, +44 (0)20 7946 0958. Numbers
    must not touch other letters or digits. Two numbers separated only by
    a space read as one and are not found (ours)."""

    CANDIDATES = re.compile(
        r"(?<![A-Za-z0-9+])"
        r"(?:(?P<intl>\+|00)[ ]?)?"
        r"\(?\d(?:[ .\-]?\(?\d\)?)*"
        r"(?![A-Za-z0-9])",
        re.ASCII,
    )
    MIN_DIGITS = 6
    MAX_DIGITS = 16

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.country_code = config.get("country_code")
        if not isinstance(self.country_code, str) or not re.fullmatch(
            r"[1-9]\d{0,2}", self.country_code
        ):
            raise MacieException(
                f"country_code must be 1 to 3 digits, not {self.country_code!r}"
            )
        self.trunk = config.get("trunk")
        if not isinstance(self.trunk, str) or not re.fullmatch(r"\d?", self.trunk):
            raise MacieException(
                f"trunk must be one digit or empty, not {self.trunk!r}"
            )
        self.trunk_required = config.get("trunk_required")
        if not isinstance(self.trunk_required, bool):
            raise MacieException("trunk_required must be true or false")
        if self.trunk_required and self.trunk == "":
            raise MacieException("trunk_required needs a trunk")
        formats = config.get("nsn_formats")
        if not isinstance(formats, list) or len(formats) == 0:
            raise MacieException("nsn_formats must be a non-empty list")
        self.nsn = re.compile(
            "(?:"
            + "|".join(FormatDetector.compile_format(text=f) for f in formats)
            + ")"
        )

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            if self.is_phone(text=m.group(0)):
                found.append((m.start(), m.end()))
        return found

    def keyword_exempt(self, *, cell: str, start: int, end: int) -> bool:
        """a number written with the country code needs no keyword"""
        return self._international(text=cell[start:end])

    @classmethod
    def _international(cls, *, text: str) -> bool:
        return text.startswith("+") or text.startswith("00")

    def is_phone(self, *, text: str) -> bool:
        digits = re.sub(r"\D", "", text)
        if text.startswith("00"):
            digits = digits[2:]
        if not self.MIN_DIGITS <= len(digits) <= self.MAX_DIGITS:
            return False
        if self._international(text=text):
            if not digits.startswith(self.country_code):
                return False
            nsn = digits[len(self.country_code) :]
            if self._valid(nsn=nsn):
                return True
            #
            # +44 (0)20 ...: the trunk kept in parentheses
            #
            return (
                self.trunk != ""
                and f"({self.trunk})" in text.replace(" ", "")
                and nsn.startswith(self.trunk)
                and self._valid(nsn=nsn[len(self.trunk) :])
            )
        if self.trunk and digits.startswith(self.trunk):
            if self._valid(nsn=digits[len(self.trunk) :]):
                return True
        if self.trunk_required:
            return False
        return self._valid(nsn=digits)

    def _valid(self, *, nsn: str) -> bool:
        return self.nsn.fullmatch(nsn) is not None
