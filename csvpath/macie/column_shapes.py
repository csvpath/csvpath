import re
from collections import Counter

from .util.mask_utility import MaskUtility as maut


class ColumnShapes:
    """what the NAME and ADDRESS check knows about one column
    (specs/macie/jev-names-addresses-design.md): its masked shapes, with
    the case-keeping mask, and how many cells are filled and distinct. No
    value is kept, only a hash of each, to count the distinct ones.

    Memory is capped for big files: at most MAX_SHAPES shapes are counted
    one by one, the rest together as other; distinct values are counted up
    to MAX_DISTINCT, and past that the count is a floor."""

    MAX_SHAPES = 500
    MAX_DISTINCT = 100_000
    TOP = 6
    #
    # a postal code, after a space or a comma, in the case-keeping mask: 4
    # or 5 digits (AU, DE, FR, IT, ES, US), the US ZIP+4, Canada's A#A #A#,
    # the UK's outward and inward codes. Not at the start of the value:
    # a street number, a ZIP code alone or a date is no address
    #
    POSTCODE = re.compile(
        r"[ ,]\s*(?:#{4,5}(?:-####)?|A#A ?#A#|A{1,2}#[A#]? ?#A{2})(?=$|[ ,])"
    )

    def __init__(self, *, column: int, column_name: str) -> None:
        if not isinstance(column, int) or isinstance(column, bool) or column < 1:
            raise ValueError(f"column must be a positive int, not {column!r}")
        if column_name is not None and not isinstance(column_name, str):
            raise TypeError(
                f"column_name must be a str or None, not {type(column_name)}"
            )
        self.column = column
        self.column_name = column_name
        self.rows = 0
        self.filled = 0
        self.shapes: Counter = Counter()
        self.other = 0
        self._hashes: set[int] = set()
        self.distinct_capped = False

    def add(self, *, cell: str) -> None:
        """one line's cell in this column"""
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        self.rows += 1
        if cell.strip() == "":
            return
        self.filled += 1
        if len(self._hashes) < self.MAX_DISTINCT:
            self._hashes.add(hash(cell))
        else:
            self.distinct_capped = True
        shape = maut.mask_case(text=cell)
        if shape in self.shapes or len(self.shapes) < self.MAX_SHAPES:
            self.shapes[shape] += 1
        else:
            self.other += 1

    @property
    def distinct(self) -> int:
        return len(self._hashes)

    def top(self, *, n: int = TOP) -> list[tuple[str, int]]:
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError(f"n must be a positive int, not {n!r}")
        return self.shapes.most_common(n)

    def may_hold_postcodes(self) -> bool:
        """True if one of the common shapes has a postal code after a space
        or comma: the screen before an ADDRESS question, so a street or a
        city alone costs no question"""
        return any(self.POSTCODE.search(s) for s, _ in self.top())

    def to_dict(self) -> dict:
        return {
            "column": self.column,
            "columnName": self.column_name,
            "rows": self.rows,
            "filled": self.filled,
            "distinct": self.distinct,
            "distinctCapped": self.distinct_capped,
            "shapes": [{"shape": s, "count": n} for s, n in self.top()],
        }
