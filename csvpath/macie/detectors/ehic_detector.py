import re

from ..macie_exceptions import MacieException


class EhicDetector:
    """finds European Health Insurance Card numbers in a cell, our stand-in
    for Macie's EUROPEAN_HEALTH_INSURANCE_CARD_NUMBER and
    FINLAND_EUROPEAN_HEALTH_INSURANCE_NUMBER. Macie publishes only the
    keywords. The format is ours: the card's identification number, 20
    digits, an ISO/IEC 7812 health card number of 80 and the issuing
    country's ISO 3166 numeric code (Finland 246), then 15 digits. Written
    contiguous, as two blocks of 10 (Microsoft Purview's description of
    Finland's), or as four blocks of 5, with spaces or hyphens. No check
    digit is verified: we have found none published. The catalog
    detector's data:

        countries   the ISO 3166 numeric codes, 3 digits each, of the
                    countries whose cards count

    The personal identification number also printed on the card has a
    different shape in every country, and is not detected. Numbers must
    not touch other letters or digits."""

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = ("countries",)

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        countries = config.get("countries")
        if not isinstance(countries, list) or len(countries) == 0:
            raise MacieException(
                f"countries must be a non-empty list, not {countries!r}"
            )
        for c in countries:
            if not (isinstance(c, str) and len(c) == 3 and c.isascii() and c.isdigit()):
                raise MacieException(f"A country must be 3 ASCII digits, not {c!r}")
        self.countries = set(countries)

    CANDIDATES = re.compile(
        r"(?<![A-Za-z0-9])(?:"
        r"(?P<flat>\d{20})"
        r"|(?P<ten>\d{10}(?P<s1>[ -])\d{10})"
        r"|(?P<five>\d{5}(?P<s2>[ -])\d{5}(?P=s2)\d{5}(?P=s2)\d{5})"
        r")(?![A-Za-z0-9])",
        re.ASCII,
    )

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            digits = re.sub(r"[ -]", "", m.group(0))
            if digits[:2] == "80" and digits[2:5] in self.countries:
                found.append((m.start(), m.end()))
        return found
