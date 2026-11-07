import datetime
import re

from ..util.checksum_utility import ChecksumUtility as chut


class MxCurpDetector:
    """finds Mexican CURPs in a cell, our stand-in for Macie's
    MEXICO_CURP_NUMBER. Macie publishes only the keywords. The format is
    ours, from RENAPO: 18 characters,

        4 letters        from the name
        6 digits         birth date, YYMMDD, a real date
        1 letter         sex, H or M (ours: also X)
        2 letters        a state code, or NE for born abroad
        3 letters        consonants from the name
        1 letter/digit   a digit for births before 2000, a letter after
        1 digit          the check digit (chut.mx_curp_check)

    Ours: X is accepted for sex, so that newer CURPs are not missed; and
    RENAPO's list of 4 letter words never issued is not applied, since
    those codes never occur. Letters may be upper or lower case. CURPs
    must not touch other letters or digits."""

    STATES = frozenset(
        """AS BC BS CC CH CL CM CS DF DG GR GT HG JC MC MN MS NE NL NT OC PL QR
        QT SL SP SR TC TL TS VZ YN ZS""".split()
    )
    CANDIDATES = re.compile(
        r"(?<![A-Za-z0-9])"
        r"[A-Z]{4}\d{6}[HMX][A-Z]{2}[A-Z]{3}[A-Z0-9]\d"
        r"(?![A-Za-z0-9])",
        re.ASCII | re.IGNORECASE,
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
            if self.is_curp(curp=m.group(0).upper()):
                found.append((m.start(), m.end()))
        return found

    def is_curp(self, *, curp: str) -> bool:
        if curp[11:13] not in self.STATES:
            return False
        century = 1900 if curp[16].isdigit() else 2000
        try:
            datetime.date(century + int(curp[4:6]), int(curp[6:8]), int(curp[8:10]))
        except ValueError:
            return False
        return chut.mx_curp_check(curp=curp[:17]) == curp[17]
