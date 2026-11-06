import re

from ..checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException
from .us_ssn_detector import UsSsnDetector


class UsIdDetector:
    """finds US health and taxpayer identifiers in a cell, our stand-in for
    Macie's US_DRUG_ENFORCEMENT_AGENCY_NUMBER, USA_MEDICARE_BENEFICIARY_
    IDENTIFIER, USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER,
    USA_HEALTH_INSURANCE_CLAIM_NUMBER, USA_NATIONAL_DRUG_CODE and
    USA_HEALTHCARE_PROCEDURE_CODE. Macie publishes only their keywords; the
    formats are ours, from the issuers. The forms, which the catalog
    detector's data names:

        dea     DEA: a registrant type letter, a letter or 9 (the
                registrant's initial), 7 digits; the last a check digit
                (chut.us_dea): AB1234563. Ours: any type letter, so new
                registrant types are not missed
        mbi     Medicare Beneficiary Identifier (CMS): 11 characters,
                1-9, a letter, a letter or digit, a digit, a letter, a
                letter or digit, a digit, two letters, two digits; letters
                never S L O I B Z. Dashes after the 4th and 7th are
                allowed: 1EG4-TE5-MK73
        itin    ITIN (IRS): 9, 2 digits, middle digits 50-65, 70-88, 90-92
                or 94-99, 4 digits; hyphens or spaces (one separator) or
                none: 912-90-3456
        hicn    HICN (CMS): an SSN, by the SSA rules, and a beneficiary
                code of a letter and an optional letter or digit:
                123-45-6789A, 123456789B1. Railroad Retirement Board
                numbers are not detected (the entry is partial)
        ndc     NDC (FDA): 10 digits as 4-4-2, 5-3-2 or 5-4-1 with
                hyphens, the 11 digit 5-4-2 billing form, or 10 or 11
                digits contiguous
        hcpcs   HCPCS (CMS): Level II, a letter A-V and 4 digits (J1234);
                and, as Macie's keywords include current procedural
                terminology, CPT codes: 5 digits, or 4 digits and F, T or U

    exclusions, in the catalog data, are never reported. Letters may be
    upper or lower case. Identifiers must not touch other letters or
    digits."""

    MBI_LETTER = "[AC-HJKMNP-RT-Y]"
    FORMS = {
        "dea": re.compile(
            r"(?<![A-Za-z0-9])(?P<letters>[A-Za-z][A-Za-z9])(?P<digits>\d{7})(?![A-Za-z0-9])",
            re.ASCII,
        ),
        "mbi": re.compile(
            r"(?<![A-Za-z0-9])"
            rf"[1-9]{MBI_LETTER}(?:{MBI_LETTER}|\d)\d"
            r"(?P<s>-?)"
            rf"{MBI_LETTER}(?:{MBI_LETTER}|\d)\d"
            r"(?P=s)"
            rf"{MBI_LETTER}{{2}}\d{{2}}"
            r"(?![A-Za-z0-9])",
            re.ASCII | re.IGNORECASE,
        ),
        "itin": re.compile(
            r"(?<![0-9])9\d{2}(?P<s>[- ]?)"
            r"(?:5\d|6[0-5]|7\d|8[0-8]|9[0-2]|9[4-9])"
            r"(?P=s)\d{4}(?![0-9])",
            re.ASCII,
        ),
        "hicn": re.compile(
            r"(?<![A-Za-z0-9])"
            r"(?:(?P<a1>\d{3})(?P<s>[ -])(?P<g1>\d{2})(?P=s)(?P<n1>\d{4})"
            r"|(?P<a2>\d{3})(?P<g2>\d{2})(?P<n2>\d{4}))"
            r"[- ]?(?P<code>[A-Za-z][A-Za-z0-9]?)"
            r"(?![A-Za-z0-9])",
            re.ASCII,
        ),
        "ndc": re.compile(
            r"(?<![0-9-])(?:"
            r"\d{4}-\d{4}-\d{2}|\d{5}-\d{3}-\d{2}|\d{5}-\d{4}-\d{1,2}|\d{10,11}"
            r")(?![0-9-])",
            re.ASCII,
        ),
        "hcpcs": re.compile(
            r"(?<![A-Za-z0-9])(?:[A-Va-v]\d{4}|\d{5}|\d{4}[FTUftu])(?![A-Za-z0-9])",
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
        exclusions = config.get("exclusions") or []
        if not isinstance(exclusions, list) or not all(
            isinstance(e, str) and e.strip() != "" for e in exclusions
        ):
            raise MacieException("exclusions must be a list of non-empty strings")
        self.exclusions = frozenset(e.upper() for e in exclusions)
        self.candidates = self.FORMS[self.form]
        self.ssn = UsSsnDetector(config={})

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.candidates.finditer(cell):
            compact = re.sub(r"[- ]", "", m.group(0)).upper()
            if compact in self.exclusions or not self.is_valid(match=m):
                continue
            found.append((m.start(), m.end()))
        return found

    def is_valid(self, *, match: re.Match) -> bool:
        if self.form == "dea":
            return chut.us_dea(digits=match.group("digits"))
        if self.form == "hicn":
            return self.ssn.is_ssn(
                area=match.group("a1") or match.group("a2"),
                group=match.group("g1") or match.group("g2"),
                serial=match.group("n1") or match.group("n2"),
            )
        return True
