import hashlib
import re

from .util.mask_utility import MaskUtility as maut


class ColumnFacts:
    """what a run can say exactly about one identifier's flagged cells in
    one column, for a Jev review (specs/macie/jev-review-build.md): how
    many cells and occurrences, how many distinct cells, whether the
    cells are consecutive numbers, and a few masked samples, one per
    masked shape (four SSNs alone in their cells are one sample).

    No value is kept: distinct cells are counted by a digest, samples are
    masked when added, and the numbers kept for the consecutive check stay
    in memory only. Distinct cells stop being counted past MAX_DISTINCT,
    and the facts then say "at least"."""

    MAX_DISTINCT = 10000
    MAX_SAMPLES = 3
    #
    # the cell must be only these and digits for the consecutive check
    #
    SEPARATORS = re.compile(r"[\s\-./()]")
    #
    # at or below this share of distinct cells, the same few values repeat
    #
    FEW = 0.05

    def __init__(
        self, *, identifier: str, column: int, column_name: str, why: str | None = None
    ) -> None:
        if not isinstance(identifier, str) or identifier.strip() == "":
            raise ValueError("identifier must be a non-empty str")
        if not isinstance(column, int) or isinstance(column, bool) or column < 1:
            raise ValueError(f"column must be a positive int, not {column!r}")
        if not isinstance(column_name, str):
            raise TypeError(f"column_name must be a str, not {type(column_name)}")
        if why is not None and (not isinstance(why, str) or why.strip() == ""):
            raise ValueError("why must be a non-empty str when given")
        self.identifier = identifier
        #
        # why the scan flagged the cells, in words, e.g. "the column header
        # holds a keyword"; the second Jev experiment asked with it
        #
        self.why = why
        self.column = column
        self.column_name = column_name
        self.cells = 0
        self.occurrences = 0
        self._digests = set()
        self.capped = False
        self._numbers = set()
        self._all_numbers = True
        self.samples = []

    def add(self, *, cell: str, occurrences: int) -> None:
        """one flagged cell holding occurrences occurrences"""
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        if (
            not isinstance(occurrences, int)
            or isinstance(occurrences, bool)
            or occurrences < 1
        ):
            raise ValueError(f"occurrences must be a positive int, not {occurrences!r}")
        self.cells += 1
        self.occurrences += occurrences
        digest = hashlib.blake2b(cell.encode("utf-8"), digest_size=16).digest()
        new = digest not in self._digests
        if new and not self.capped:
            if len(self._digests) >= self.MAX_DISTINCT:
                self.capped = True
            else:
                self._digests.add(digest)
        if self._all_numbers:
            digits = self.SEPARATORS.sub("", cell)
            #
            # past MAX_DISTINCT the check is given up, as distinct counting
            # is: consecutive is then False, never a guess
            #
            if (
                digits.isdigit()
                and len(digits) <= 18
                and len(self._numbers) < self.MAX_DISTINCT
            ):
                self._numbers.add(int(digits))
            else:
                self._all_numbers = False
                self._numbers = set()
        if new and len(self.samples) < self.MAX_SAMPLES:
            masked = maut.mask_cell(text=cell)
            if masked not in self.samples:
                self.samples.append(masked)

    @property
    def distinct(self) -> int:
        return len(self._digests)

    @property
    def consecutive(self) -> bool:
        """every flagged cell is a number, all different, with no gaps"""
        if not self._all_numbers or self.capped or self.cells < 3:
            return False
        n = len(self._numbers)
        return n == self.cells and max(self._numbers) - min(self._numbers) + 1 == n

    def facts(self) -> list[str]:
        """the plain-words facts the second Jev experiment used"""
        facts = []
        cells, distinct = self.cells, self.distinct
        at_least = "at least " if self.capped else ""
        if cells > 1 and distinct == 1:
            facts.append(f"Every one of the {cells} flagged values is the same value.")
        elif cells > 1 and distinct / cells <= self.FEW:
            facts.append(
                f"Only {at_least}{distinct} distinct values among {cells} flagged "
                "cells: the same few values repeat."
            )
        elif cells > 1 and distinct == cells:
            facts.append("Every flagged value is different.")
        if self.consecutive:
            facts.append(
                "The flagged values are consecutive: each is the one before plus one."
            )
        return facts

    def to_dict(self) -> dict:
        return {
            "identifier": self.identifier,
            "column": self.column,
            "columnName": self.column_name,
            "why": self.why,
            "cells": self.cells,
            "occurrences": self.occurrences,
            "distinct": self.distinct,
            "distinct_capped": self.capped,
            "consecutive": self.consecutive,
            "samples": list(self.samples),
            "facts": self.facts(),
        }
