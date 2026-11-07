import re

from ..util.checksum_utility import ChecksumUtility as chut


class UdiDetector:
    """finds medical device unique device identifiers in a cell, our
    stand-in for Macie's MEDICAL_DEVICE_UDI. Macie: UDIs in the formats the
    US FDA accepts, GS1, HIBCC and ICCBBA (ISBT 128), near a keyword. Ours,
    in their human readable forms:

        gs1     (01) and a GTIN-14 with its GS1 check digit
                (chut.gs1_check), optionally followed by production
                identifiers: (11) or (17) and a YYMMDD date, (10) a lot or
                (21) a serial number of up to 20 characters, e.g.
                (01)00614141999996(17)250101(10)A1
        hibcc   + and a token whose last character is the HIBCC mod 43
                check character over everything before it
                (chut.hibcc_mod43). The primary data, before any /, is a
                labeler code (a letter and 3 letters or digits), a product
                code of 1 to 18 letters or digits and a unit of measure
                digit, e.g. +A123BJC5D6E71G

    ISBT 128 (ICCBBA) is not detected yet. Identifiers must not touch other
    letters or digits; the HIBCC token runs to the next space or a
    character HIBCC does not use."""

    GS1 = re.compile(
        r"(?<![A-Za-z0-9)])\(01\)(?P<gtin>\d{14})"
        r"(?:\((?:11|17)\)\d{6}|\((?:10|21)\)[!-'*-~]{1,20})*"
        r"(?![A-Za-z0-9(])",
        re.ASCII,
    )
    HIBCC = re.compile(
        r"(?<![A-Za-z0-9$+%./-])\+(?P<token>[A-Z0-9$+%./-]{5,})(?![A-Za-z0-9$+%./-])",
        re.ASCII,
    )
    HIBCC_PRIMARY = re.compile(r"[A-Z][A-Z0-9]{3}[A-Z0-9]{1,18}[0-9]", re.ASCII)

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
        for m in self.GS1.finditer(cell):
            if chut.gs1_check(digits=m.group("gtin")):
                found.append((m.start(), m.end()))
        for m in self.HIBCC.finditer(cell):
            token = m.group("token")
            primary = token[:-1].split("/", 1)[0]
            if self.HIBCC_PRIMARY.fullmatch(primary) is None:
                continue
            if chut.hibcc_mod43(text="+" + token[:-1]) == token[-1]:
                found.append((m.start(), m.end()))
        return sorted(found)
