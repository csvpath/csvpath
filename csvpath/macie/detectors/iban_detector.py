import re

from ..util.checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class IbanDetector:
    """finds one country's International Bank Account Numbers in a cell,
    our stand-in for Macie's <COUNTRY>_BANK_ACCOUNT_NUMBER identifiers. The
    detector takes the country code as its parameter, e.g. "iban:GB" in the
    catalog and the csvpath.

    Macie: up to 34 alphanumeric characters, ISO 13616, with no separator or
    with space or hyphen separators, validated by Modulus 97. Ours: the
    country's IBAN length from the catalog, and separators only in the
    printed layout of groups of four, one separator throughout. Letters may
    be upper or lower case."""

    TAKES_PARAMETER = True

    def __init__(self, *, config: dict, parameter: str | None = None) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        lengths = config.get("lengths")
        if not isinstance(lengths, dict) or len(lengths) == 0:
            raise MacieException("iban needs a lengths table of country code to length")
        if not isinstance(parameter, str) or parameter not in lengths:
            raise MacieException(
                f"iban needs a country code from its lengths table, not {parameter!r}"
            )
        self.country = parameter
        self.length = lengths[parameter]
        if not isinstance(self.length, int) or not 15 <= self.length <= 34:
            raise MacieException(
                f"iban length for {parameter} must be an int from 15 to 34, not {self.length!r}"
            )
        rest = self.length - 4
        groups, last = divmod(rest, 4)
        if last == 0:
            groups, last = groups - 1, 4
        cc = re.escape(self.country)
        self.candidates = re.compile(
            r"(?<![A-Za-z0-9])(?:"
            rf"{cc}\d{{2}}[A-Za-z0-9]{{{rest}}}"
            rf"|{cc}\d{{2}}(?P<s>[ -])(?:[A-Za-z0-9]{{4}}(?P=s)){{{groups}}}[A-Za-z0-9]{{{last}}}"
            r")(?![A-Za-z0-9])",
            re.ASCII | re.IGNORECASE,
        )

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        """the (start, end) of every IBAN for the country in the cell"""
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.candidates.finditer(cell):
            text = re.sub(r"[ -]", "", m.group(0))
            if text[:2].upper() == self.country and chut.iban_mod97(iban=text):
                found.append((m.start(), m.end()))
        return found
