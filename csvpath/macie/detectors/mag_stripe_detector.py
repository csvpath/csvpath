import re

from ..checksum_utility import ChecksumUtility as chut


class MagStripeDetector:
    """finds payment card magnetic stripe data in a cell, our stand-in for
    Macie's CREDIT_CARD_MAGNETIC_STRIPE. Macie publishes the keywords and
    that tracks 1 and 2 are supported. The format is ours, from ISO/IEC
    7813:

        track 1   %B, the card number, ^, the name (2 to 26 characters),
                  ^, the expiry YYMM, a 3 digit service code, discretionary
                  data, ?: %B4111111111111111^DOE/JOHN^2512101000000000?
        track 2   ;, the card number, =, the expiry YYMM, the service code,
                  discretionary digits, ?: ;4111111111111111=2512101?

    The start and end sentinels (% ; ?) may be missing, as in stored
    data. The card number is 12 to 19 digits and must pass Luhn; the
    expiry month must be 01 to 12."""

    CANDIDATES = re.compile(
        r"(?:%?B(?P<pan1>\d{12,19})\^[A-Za-z0-9 /.'-]{2,26}\^(?P<exp1>\d{4})\d{3}[^?\s^]*\??"
        r"|(?<![0-9])(?:;)?(?P<pan2>\d{12,19})=(?P<exp2>\d{4})\d{3}\d*\??)",
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
            pan = m.group("pan1") or m.group("pan2")
            expiry = m.group("exp1") or m.group("exp2")
            if chut.luhn(digits=pan) and 1 <= int(expiry[2:]) <= 12:
                found.append((m.start(), m.end()))
        return found
