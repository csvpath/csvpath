import datetime
import re

from ..macie_exceptions import MacieException


class MxRfcDetector:
    """finds Mexican RFCs in a cell, our stand-in for Macie's
    MEXICO_INDIVIDUAL_RFC_NUMBER and MEXICO_ORGANIZATION_RFC_NUMBER.
    Macie publishes the keywords, and that XAXX010101000 and
    XEXX010101000, common examples, are never reported. The format is
    ours, from the SAT:

        individual    4 letters, a YYMMDD date, 3 characters: GODE561231GR8
        organization  3 letters, a YYMMDD date, 3 characters: MAB9307148T4

    The letters may include Ñ and &. The date must be a real date. A space
    or hyphen may separate the parts: GODE 561231 GR8, MAB-930714-8T4.

    Ours: the last character is a check digit, but it is NOT checked.
    About 1.5% of RFCs in use have a wrong one (python-stdnum's note), and
    a check would miss them (David, 2026-11-03). Letters may be upper or
    lower case. RFCs must not touch other letters or digits. The catalog
    detector's data gives the form:

        form    "individual" or "organization"
    """

    LETTERS = {"individual": 4, "organization": 3}
    EXCLUSIONS = frozenset({"XAXX010101000", "XEXX010101000"})

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.form = config.get("form")
        if self.form not in self.LETTERS:
            raise MacieException(
                f"form must be one of {sorted(self.LETTERS)}, not {self.form!r}"
            )
        n = self.LETTERS[self.form]
        self.candidates = re.compile(
            r"(?<![A-Za-z0-9&ÑñÁÉÍÓÚáéíóú])"
            rf"(?P<name>[A-Za-z&Ññ]{{{n}}})(?P<s>[- ]?)(?P<date>[0-9]{{6}})(?P=s)"
            r"(?P<key>[A-Za-z0-9]{3})"
            r"(?![A-Za-z0-9&Ññ])"
        )

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.candidates.finditer(cell):
            rfc = (m.group("name") + m.group("date") + m.group("key")).upper()
            if rfc not in self.EXCLUSIONS and self.is_date(date=m.group("date")):
                found.append((m.start(), m.end()))
        return found

    def is_date(self, *, date: str) -> bool:
        #
        # two digits of the year: a real date in the 1900s or the 2000s
        #
        for century in (1900, 2000):
            try:
                datetime.date(century + int(date[:2]), int(date[2:4]), int(date[4:]))
                return True
            except ValueError:
                continue
        return False
