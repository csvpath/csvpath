import re

from ..checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class EsIdDetector:
    """finds Spanish DNI or NIE numbers in a cell, our stand-in for Macie's
    SPAIN_DNI_NUMBER and SPAIN_NIE_NUMBER. Macie publishes the keywords,
    and for DNIs that 99999999, 99.999.999 and all zeroes are never
    reported. The format is ours, from Spain's Ministerio del Interior:

        dni   8 digits, optionally dotted (12.345.678), then the control
              letter, optionally after a hyphen or space: 12345678Z,
              12.345.678-Z
        nie   X, Y or Z, 7 digits, then the control letter, with an
              optional hyphen or space after the first letter and before
              the last: X1234567L, X-1234567-L

    The control letter is the number mod 23 (chut.es_id_letter). Letters
    may be upper or lower case. Numbers must not touch other letters or
    digits. The catalog detector's data gives the form:

        form    "dni" or "nie"
    """

    FORMS = {
        "dni": re.compile(
            r"(?<![A-Za-z0-9.])"
            r"(?P<number>\d{8}|\d{2}\.\d{3}\.\d{3})"
            r"[- ]?(?P<letter>[A-Za-z])"
            r"(?![A-Za-z0-9])",
            re.ASCII,
        ),
        "nie": re.compile(
            r"(?<![A-Za-z0-9.])"
            r"(?P<lead>[XYZxyz])[- ]?(?P<number>\d{7})"
            r"[- ]?(?P<letter>[A-Za-z])"
            r"(?![A-Za-z0-9])",
            re.ASCII,
        ),
    }

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.form = config.get("form")
        if self.form not in self.FORMS:
            raise MacieException(
                f"form must be one of {sorted(self.FORMS)}, not {self.form!r}"
            )
        self.candidates = self.FORMS[self.form]

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.candidates.finditer(cell):
            number = m.group("number").replace(".", "")
            lead = m.groupdict().get("lead") or ""
            if self.is_valid(number=number, lead=lead, letter=m.group("letter")):
                found.append((m.start(), m.end()))
        return found

    def is_valid(self, *, number: str, lead: str, letter: str) -> bool:
        #
        # Macie never reports all zeroes, nor the DNI example 99999999
        #
        if set(number) == {"0"} or (self.form == "dni" and number == "99999999"):
            return False
        return chut.es_id_letter(number=f"{lead}{number}") == letter.upper()
