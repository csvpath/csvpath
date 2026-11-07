import datetime
import re

from ..util.checksum_utility import ChecksumUtility as chut


class CaHealthDetector:
    """finds Canadian provincial health numbers in a cell, our stand-in for
    Macie's CANADA_HEALTH_NUMBER. Macie publishes only the keywords, which
    name British Columbia's MSP and PHN and Quebec's soins de sante. The
    forms are ours, the provinces whose numbers have a published structure:

        bc   British Columbia PHN: 10 digits, the first 9, a mod 11 check
             digit (chut.ca_bc_phn), as 9698658215 or 9698 658 215
        on   Ontario health number: 10 digits with a Luhn check digit, as
             9876543217 or 9876-543-217, optionally with a one or two
             letter version code after it
        qc   Quebec RAMQ number: 4 letters (from the surname and first
             name), the birth date as YYMMDD with 50 added to the month for
             women, and 2 digits, as ABCD 8502 1512

    The other provinces' numbers are 8 to 12 digits with no published
    check; near a broad keyword such as health card they would match any
    digit run of that length, so they are not included. Numbers must not
    touch other letters or digits. Where forms overlap (a BC PHN that also
    passes Luhn), the longest match at a position is the one occurrence."""

    CANDIDATES = [
        (
            re.compile(
                r"(?<![A-Za-z0-9])(?P<a>9\d{3})(?P<s>[ -]?)(?P<b>\d{3})(?P=s)(?P<c>\d{3})(?![A-Za-z0-9])",
                re.ASCII,
            ),
            "bc",
        ),
        (
            re.compile(
                r"(?<![A-Za-z0-9])(?P<a>\d{4})(?P<s>[ -]?)(?P<b>\d{3})(?P=s)(?P<c>\d{3})(?:[ -]?[A-Za-z]{1,2})?(?![A-Za-z0-9])",
                re.ASCII,
            ),
            "on",
        ),
        (
            re.compile(
                r"(?<![A-Za-z0-9])[A-Za-z]{4} ?(?P<yy>\d{2})(?P<mm>\d{2}) ?(?P<dd>\d{2})\d{2}(?![A-Za-z0-9])",
                re.ASCII,
            ),
            "qc",
        ),
    ]

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
        spans = []
        for pattern, form in self.CANDIDATES:
            for m in pattern.finditer(cell):
                if self._valid(match=m, form=form):
                    spans.append((m.start(), m.end()))
        found = []
        for start, end in sorted(spans, key=lambda s: (s[0], -(s[1] - s[0]))):
            if found and start < found[-1][1]:
                continue
            found.append((start, end))
        return found

    @classmethod
    def _valid(cls, *, match: re.Match, form: str) -> bool:
        if form == "qc":
            month = int(match.group("mm"))
            if month > 50:
                month = month - 50
            #
            # any century: a two digit year is read as 20yy, which has the
            # same leap years as 19yy except 00
            #
            try:
                datetime.date(
                    2000 + int(match.group("yy")), month, int(match.group("dd"))
                )
                return True
            except ValueError:
                return False
        digits = match.group("a") + match.group("b") + match.group("c")
        if form == "bc":
            return chut.ca_bc_phn(digits=digits)
        return chut.luhn(digits=digits)
