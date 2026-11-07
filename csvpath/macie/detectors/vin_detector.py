import re


class VinDetector:
    """finds vehicle identification numbers in a cell, our stand-in for
    Macie's VEHICLE_IDENTIFICATION_NUMBER. Macie: a 17-character sequence
    that adheres to ISO 3779 and 3780, designed for worldwide use.

    Ours: 17 characters of the VIN alphabet (digits and capital letters
    except I, O and Q), not touching other letters or digits, with a
    model-year character in position 10 (not U, Z or 0). The North American
    check digit in position 9 is NOT required, because VINs from elsewhere
    don't have one."""

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
            if any(c.isdigit() for c in text) and any(c.isalpha() for c in text):
                found.append((m.start(), m.end()))
        return found
