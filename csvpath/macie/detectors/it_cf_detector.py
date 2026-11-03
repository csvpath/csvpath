import re

from ..checksum_utility import ChecksumUtility as chut


class ItCfDetector:
    """finds Italian Codice Fiscale codes for people in a cell, our
    stand-in for Macie's ITALY_NATIONAL_IDENTIFICATION_NUMBER. Macie
    publishes only the keywords. The format is ours, from the Agenzia delle
    Entrate: 16 characters,

        6 letters    from the surname and name
        2 digits     birth year
        1 letter     birth month, A B C D E H L M P R S T
        2 digits     birth day, plus 40 for women
        1 letter, 3 digits   the place of birth
        1 letter     the check letter (chut.it_cf_check)

    Where codes would clash, digits are replaced by L M N P Q R S T U V
    (omocodia), so those letters are accepted for any digit. The day must
    be a real day of the month. Letters may be upper or lower case. Codes
    must not touch other letters or digits.

    Not detected: the 11 digit codice fiscale of organizations (the same
    as their partita IVA). The catalog entry is partial."""

    D = "[0-9LMNPQRSTUV]"
    CANDIDATES = re.compile(
        r"(?<![A-Za-z0-9])"
        rf"[A-Z]{{6}}{D}{{2}}[ABCDEHLMPRST]{D}{{2}}[A-Z]{D}{{3}}[A-Z]"
        r"(?![A-Za-z0-9])",
        re.ASCII | re.IGNORECASE,
    )
    OMOCODIA = str.maketrans("LMNPQRSTUV", "0123456789")
    MONTHS = "ABCDEHLMPRST"
    DAYS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.CANDIDATES.finditer(cell):
            if self.is_cf(code=m.group(0).upper()):
                found.append((m.start(), m.end()))
        return found

    def is_cf(self, *, code: str) -> bool:
        year = int(code[6:8].translate(self.OMOCODIA))
        month = self.MONTHS.index(code[8])
        day = int(code[9:11].translate(self.OMOCODIA)) % 40
        #
        # only two digits of the year: 29 February is allowed in years
        # that can be leap years
        #
        last = self.DAYS[month]
        if month == 1 and year % 4 != 0:
            last = 28
        if not 1 <= day <= last:
            return False
        return chut.it_cf_check(code=code[:15]) == code[15]
