import re

from ..util.checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class EsIdDetector:
    """finds Spanish DNI, NIE, NIF or CIF numbers in a cell, our stand-in
    for Macie's SPAIN_DNI_NUMBER, SPAIN_NIE_NUMBER, SPAIN_NIF_NUMBER and
    SPAIN_TAX_IDENTIFICATION_NUMBER. Macie publishes the keywords, and for
    DNIs that 99999999, 99.999.999 and all zeroes are never reported. The
    formats are ours, from Spain's Ministerio del Interior and Agencia
    Tributaria:

        dni   8 digits, optionally dotted (12.345.678), then the control
              letter, optionally after a hyphen or space: 12345678Z,
              12.345.678-Z
        nie   X, Y or Z, 7 digits, then the control letter, with an
              optional hyphen or space after the first letter and before
              the last: X1234567L, X-1234567-L
        nif   a person's NIF: the DNI form, or K, L or M, 7 digits and a
              control letter (the DNI's, over the 7 digits): M1234567L.
              NIEs are left to the nie form, which shares the keywords,
              so a NIE is not counted twice (David, 2026-11-03)
        cif   an organization's CIF: a type letter (A B C D E F G H J N P
              Q R S U V W), 7 digits, and a control digit or letter
              (chut.es_cif): B64717838, B-6471783-8

    The DNI and NIE control letter is the number mod 23
    (chut.es_id_letter). Letters may be upper or lower case. Numbers must
    not touch other letters or digits. The catalog detector's data gives
    the form:

        form    "dni", "nie", "nif" or "cif"
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
        "nif": re.compile(
            r"(?<![A-Za-z0-9.])"
            r"(?:(?P<number>\d{8}|\d{2}\.\d{3}\.\d{3})"
            r"|(?P<lead>[KLMklm])[- ]?(?P<seven>\d{7}))"
            r"[- ]?(?P<letter>[A-Za-z])"
            r"(?![A-Za-z0-9])",
            re.ASCII,
        ),
        "cif": re.compile(
            r"(?<![A-Za-z0-9.])"
            r"(?P<lead>[ABCDEFGHJNPQRSUVWabcdefghjnpqrsuvw])[- ]?(?P<number>\d{7})"
            r"[- ]?(?P<letter>[0-9A-Ja-j])"
            r"(?![A-Za-z0-9])",
            re.ASCII,
        ),
    }

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = ("form",)

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
            groups = m.groupdict()
            number = (groups.get("number") or groups.get("seven")).replace(".", "")
            lead = groups.get("lead") or ""
            if self.is_valid(number=number, lead=lead, letter=m.group("letter")):
                found.append((m.start(), m.end()))
        return found

    def is_valid(self, *, number: str, lead: str, letter: str) -> bool:
        #
        # Macie never reports all zeroes, nor the DNI example 99999999,
        # which is also the DNI form of a NIF
        #
        if set(number) == {"0"}:
            return False
        if self.form == "cif":
            return chut.es_cif(cif=f"{lead}{number}{letter}")
        if lead.upper() in ("K", "L", "M"):
            #
            # the DNI's letter, over the 7 digits
            #
            return chut.es_id_letter(number=f"0{number}") == letter.upper()
        if self.form in ("dni", "nif") and number == "99999999":
            return False
        return chut.es_id_letter(number=f"{lead}{number}") == letter.upper()
