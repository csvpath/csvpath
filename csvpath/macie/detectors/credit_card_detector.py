import re

from ..checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class CreditCardDetector:
    """finds credit card numbers in a cell, our stand-in for Macie's
    CREDIT_CARD_NUMBER detection: 13-19 digits that pass the Luhn check and
    start with a standard prefix for the card's length, less the card
    issuers' published test numbers. The prefix table and the exclusions
    come from the catalog's credit_card detector.

    Ours, not Macie's: grouped numbers with spaces or hyphens, one separator
    throughout, in the common layouts (4-4-4-4, 4-4-4-4-3, 4-6-5, 4-6-4)."""

    #
    # longest first, so a 19-digit grouped number isn't taken as 16
    #
    CANDIDATES = re.compile(
        r"(?<!\d)(?:"
        r"\d{4}(?P<s19>[ -])\d{4}(?P=s19)\d{4}(?P=s19)\d{4}(?P=s19)\d{3}"
        r"|\d{4}(?P<s16>[ -])\d{4}(?P=s16)\d{4}(?P=s16)\d{4}"
        r"|\d{4}(?P<s15>[ -])\d{6}(?P=s15)\d{5}"
        r"|\d{4}(?P<s14>[ -])\d{6}(?P=s14)\d{4}"
        r"|\d{13,19}"
        r")(?!\d)",
        re.ASCII,
    )

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.min_length = config.get("min_length")
        self.max_length = config.get("max_length")
        for n, v in [("min_length", self.min_length), ("max_length", self.max_length)]:
            if not isinstance(v, int) or isinstance(v, bool) or v < 1:
                raise MacieException(
                    f"credit_card {n} must be a positive int, not {v!r}"
                )
        brands = config.get("brands")
        if not isinstance(brands, list) or len(brands) == 0:
            raise MacieException("credit_card needs a list of brands")
        #
        # (brand, low, high, prefix length, lengths). a single prefix is a
        # range of one
        #
        self.prefixes = []
        for b in brands:
            for p in b.get("prefixes") or []:
                low, _, high = f"{p}".partition("-")
                high = high or low
                if not (low.isdigit() and high.isdigit() and len(low) == len(high)):
                    raise MacieException(f"Bad prefix {p!r} for {b.get('brand')}")
                lengths = b.get("lengths")
                if not isinstance(lengths, list) or len(lengths) == 0:
                    raise MacieException(f"Brand {b.get('brand')} needs lengths")
                self.prefixes.append(
                    (b.get("brand"), int(low), int(high), len(low), set(lengths))
                )
        exclusions = config.get("exclusions") or []
        if not isinstance(exclusions, list):
            raise MacieException("credit_card exclusions must be a list")
        self.exclusions = set(exclusions)

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        """the (start, end) of every credit card number in the cell"""
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            digits = re.sub(r"[ -]", "", m.group(0))
            if self.is_card(digits=digits):
                found.append((m.start(), m.end()))
        return found

    def is_card(self, *, digits: str) -> bool:
        if not self.min_length <= len(digits) <= self.max_length:
            return False
        if digits in self.exclusions:
            return False
        if self.brand(digits=digits) is None:
            return False
        return chut.luhn(digits=digits)

    def brand(self, *, digits: str) -> str | None:
        """the first brand whose prefix and lengths fit, or None"""
        for brand, low, high, size, lengths in self.prefixes:
            if len(digits) in lengths and low <= int(digits[:size]) <= high:
                return brand
        return None
