import re


class VinDetector:
    """finds vehicle identification numbers in a cell, our stand-in for
    Macie's VEHICLE_IDENTIFICATION_NUMBER. Macie: a 17-character sequence
    that adheres to ISO 3779 and 3780, designed for worldwide use.

    Ours: 17 characters of the VIN alphabet (digits and capital letters
    except I, O and Q), not touching other letters or digits, with a
    model-year character in position 10 (not U, Z or 0). A North American
    VIN, one whose first character is 1 to 5, must have the right check
    digit in position 9: the seventh live probe (2026-11-18) found Macie
    does not report one with a wrong check digit. VINs from elsewhere have
    no check digit, so none is required of them."""

    #
    # 49 CFR 565: each character's value, and each position's weight
    #
    VALUES = {str(d): d for d in range(10)} | {
        c: v
        for c, v in zip(
            "ABCDEFGHJKLMNPRSTUVWXYZ",
            [1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 7, 9, 2, 3, 4, 5, 6, 7, 8, 9],
        )
    }
    WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
    NORTH_AMERICA = "12345"

    CANDIDATES = re.compile(
        r"(?<![A-Za-z0-9])[A-HJ-NPR-Z0-9]{9}[A-HJ-NPR-TV-Y1-9][A-HJ-NPR-Z0-9]{7}(?![A-Za-z0-9])",
        re.ASCII,
    )

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = ()

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            text = m.group(0)
            #
            # a VIN mixes letters and digits; 17 digits or 17 letters is
            # something else
            #
            if not (any(c.isdigit() for c in text) and any(c.isalpha() for c in text)):
                continue
            if text[0] in self.NORTH_AMERICA and not self.check_digit_ok(vin=text):
                continue
            found.append((m.start(), m.end()))
        return found

    @classmethod
    def check_digit_ok(cls, *, vin: str) -> bool:
        """the North American check digit: the weighted sum mod 11, with 10
        written as X"""
        if not isinstance(vin, str) or len(vin) != 17:
            raise ValueError(f"vin must be a 17 character str, not {vin!r}")
        total = sum(cls.VALUES[c] * w for c, w in zip(vin, cls.WEIGHTS))
        r = total % 11
        return vin[8] == ("X" if r == 10 else str(r))
