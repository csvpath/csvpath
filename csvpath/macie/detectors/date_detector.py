import datetime
import re

from ..macie_exceptions import MacieException


class DateDetector:
    """finds dates in a cell, our stand-in for Macie's DATE_OF_BIRTH and
    CREDIT_CARD_EXPIRATION. Macie: most date formats, all digits and
    digits with month names, the parts separated by spaces, slashes or
    hyphens; for card expiration also by keywords, e.g. 02/26, 02/2026,
    Feb 2026, 26-Feb and expY=2026, expM=02. The catalog detector's data
    gives the form:

        birth    a full date that is a real date:
                   5/11/1985 or 11/5/1985  (D/M/Y or M/D/Y, either reading)
                   1985-11-05               (Y-M-D)
                   5 Nov 1985, 05-Nov-85    (day, month name, year)
                   November 5, 1985         (month name, day, year)
                   1985-Nov-05              (year, month name, day)
                   19851105                 (8 digits: YYYYMMDD, DDMMYYYY or
                                             MMDDYYYY)
                 one separator throughout; years of 2 digits, or 1900-2099
        expiry   a month and a year:
                   02/26, 02-2026           (month, year)
                   Feb 2026, February-26    (month name, year)
                   26-Feb                   (year, month name)
                   expY=2026, expM=02       (Macie's keyword form, either
                                             order)
                 years of 2 digits, or 1990-2099

    Ours: month names are English, and dots are not separators, as Macie
    lists spaces, slashes and hyphens. A month and year that is part of a
    full date (12/25/2026) is not an expiry date. Dates must not touch
    other letters or digits. The keyword form is keyword exempt: its
    keywords are inside it."""

    MONTH = (
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?"
        r"|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    )
    MONTHS = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }  # fmt: skip
    LEFT = r"(?<![A-Za-z0-9/-])"
    RIGHT = r"(?![A-Za-z0-9]|[/-][0-9])"

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = ("form",)

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.form = config.get("form")
        if self.form == "birth":
            self.patterns = self._birth_patterns()
        elif self.form == "expiry":
            self.patterns = self._expiry_patterns()
        else:
            raise MacieException(f"form must be birth or expiry, not {self.form!r}")

    def _birth_patterns(self) -> list[tuple[re.Pattern, str]]:
        M, L, R = self.MONTH, self.LEFT, self.RIGHT
        y = r"(?P<y>\d{4}|\d{2})"
        return [
            (
                re.compile(
                    rf"{L}(?P<a>\d{{1,2}})(?P<s>[ /-])(?P<b>\d{{1,2}})(?P=s){y}{R}"
                ),
                "dmy_or_mdy",
            ),
            (
                re.compile(
                    rf"{L}(?P<y>\d{{4}})(?P<s>[ /-])(?P<m>\d{{1,2}})(?P=s)(?P<d>\d{{1,2}}){R}"
                ),
                "ymd",
            ),
            (
                re.compile(
                    rf"{L}(?P<d>\d{{1,2}})(?P<s>[ -])(?P<mn>{M})(?P=s){y}{R}", re.I
                ),
                "d_name_y",
            ),
            (
                re.compile(
                    rf"{L}(?P<mn>{M})[ -](?P<d>\d{{1,2}}),?[ -](?P<y>\d{{4}}){R}", re.I
                ),
                "name_d_y",
            ),
            (
                re.compile(
                    rf"{L}(?P<y>\d{{4}})(?P<s>[ -])(?P<mn>{M})(?P=s)(?P<d>\d{{1,2}}){R}",
                    re.I,
                ),
                "y_name_d",
            ),
            (re.compile(rf"{L}(?P<digits>\d{{8}}){R}"), "digits"),
        ]

    def _expiry_patterns(self) -> list[tuple[re.Pattern, str]]:
        M, L, R = self.MONTH, self.LEFT, self.RIGHT
        return [
            (re.compile(rf"{L}(?P<m>\d{{1,2}})[/-](?P<y>\d{{4}}|\d{{2}}){R}"), "my"),
            (
                re.compile(rf"{L}(?P<mn>{M})[ -]?(?P<y>\d{{4}}|\d{{2}}){R}", re.I),
                "name_y",
            ),
            (re.compile(rf"{L}(?P<y>\d{{2}})-(?P<mn>{M}){R}", re.I), "y_name"),
            (
                re.compile(
                    r"(?<![A-Za-z0-9])exp ?y ?= ?(?P<y>\d{4}|\d{2})[ ,;]*exp ?m ?= ?(?P<m>\d{1,2})(?![0-9])",
                    re.I,
                ),
                "my",
            ),
            (
                re.compile(
                    r"(?<![A-Za-z0-9])exp ?m ?= ?(?P<m>\d{1,2})[ ,;]*exp ?y ?= ?(?P<y>\d{4}|\d{2})(?![0-9])",
                    re.I,
                ),
                "my",
            ),
        ]

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        spans = []
        for pattern, kind in self.patterns:
            for m in pattern.finditer(cell):
                if self._valid(match=m, kind=kind):
                    spans.append((m.start(), m.end()))
        #
        # one occurrence per date: where shapes overlap, keep the first
        # and longest
        #
        found = []
        for start, end in sorted(spans, key=lambda s: (s[0], -(s[1] - s[0]))):
            if found and start < found[-1][1]:
                continue
            found.append((start, end))
        return found

    def keyword_exempt(self, *, cell: str, start: int, end: int) -> bool:
        """Macie's keyword form, expY=2026, expM=02, carries its own
        keywords inside the occurrence, where nearness is not measured"""
        return self.form == "expiry" and cell[start:end][:3].lower() == "exp"

    def _valid(self, *, match: re.Match, kind: str) -> bool:
        g = match.groupdict()
        if self.form == "expiry":
            month = self.MONTHS[g["mn"][:3].lower()] if g.get("mn") else int(g["m"])
            year = int(g["y"])
            return 1 <= month <= 12 and (len(g["y"]) == 2 or 1990 <= year <= 2099)
        if kind == "dmy_or_mdy":
            a, b = int(g["a"]), int(g["b"])
            return self._real(y=g["y"], m=b, d=a) or self._real(y=g["y"], m=a, d=b)
        if kind == "digits":
            s = g["digits"]
            return (
                self._real(y=s[:4], m=int(s[4:6]), d=int(s[6:]))
                or self._real(y=s[4:], m=int(s[2:4]), d=int(s[:2]))
                or self._real(y=s[4:], m=int(s[:2]), d=int(s[2:4]))
            )
        month = self.MONTHS[g["mn"][:3].lower()] if g.get("mn") else int(g["m"])
        return self._real(y=g["y"], m=month, d=int(g["d"]))

    @classmethod
    def _real(cls, *, y: str, m: int, d: int) -> bool:
        year = int(y)
        if len(y) == 4 and not 1900 <= year <= 2099:
            return False
        #
        # a two digit year is read as 20yy: the same leap years as 19yy,
        # except 00, so 29/02/00 is allowed
        #
        if len(y) == 2:
            year = 2000 + year
        try:
            datetime.date(year, m, d)
            return True
        except ValueError:
            return False
