import re

from ..checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class GroupedDigitsDetector:
    """finds fixed-length digit identifiers that are printed in groups and
    have a check digit, e.g. Canada's SIN (3-3-3, Luhn) and the UK NHS
    number (3-3-4, mod 11). Each catalog detector that uses this class
    gives its own data:

        length        the number of digits
        layouts       group sizes, e.g. [[3, 3, 3]]; the digits may also
                      be contiguous
        check         a ChecksumUtility check name, e.g. "luhn"
        first_digit_not  digits a number never starts with (optional)
        exclusions    numbers never reported, e.g. published examples

    Groups are separated by a space or a hyphen, one separator throughout.
    Numbers must not touch other digits."""

    def __init__(self, *, config: dict) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        self.length = config.get("length")
        if (
            not isinstance(self.length, int)
            or isinstance(self.length, bool)
            or self.length < 2
        ):
            raise MacieException(
                f"length must be an int of at least 2, not {self.length!r}"
            )
        self.check = config.get("check")
        if self.check not in chut.CHECKS:
            raise MacieException(
                f"check must be one of {sorted(chut.CHECKS)}, not {self.check!r}"
            )
        layouts = config.get("layouts") or []
        if not isinstance(layouts, list):
            raise MacieException("layouts must be a list of group sizes")
        alternatives = [rf"\d{{{self.length}}}"]
        for i, layout in enumerate(layouts):
            if (
                not isinstance(layout, list)
                or len(layout) < 2
                or not all(isinstance(g, int) and g > 0 for g in layout)
                or sum(layout) != self.length
            ):
                raise MacieException(
                    f"layout {layout!r} must be group sizes that add up to {self.length}"
                )
            sep = f"s{i}"
            parts = [rf"\d{{{layout[0]}}}(?P<{sep}>[ -])"]
            parts += [rf"\d{{{g}}}(?P={sep})" for g in layout[1:-1]]
            parts.append(rf"\d{{{layout[-1]}}}")
            alternatives.insert(0, "".join(parts))
        self.candidates = re.compile(
            r"(?<!\d)(?:" + "|".join(alternatives) + r")(?!\d)", re.ASCII
        )
        self.first_digit_not = set(config.get("first_digit_not") or [])
        exclusions = config.get("exclusions") or []
        if not isinstance(exclusions, list):
            raise MacieException("exclusions must be a list")
        for e in exclusions:
            if not (isinstance(e, str) and len(e) == self.length and e.isdigit()):
                raise MacieException(f"exclusion {e!r} must be {self.length} digits")
        self.exclusions = set(exclusions)

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = []
        for m in self.candidates.finditer(cell):
            digits = re.sub(r"[ -]", "", m.group(0))
            if self.is_valid(digits=digits):
                found.append((m.start(), m.end()))
        return found

    def is_valid(self, *, digits: str) -> bool:
        if digits[0] in self.first_digit_not or digits in self.exclusions:
            return False
        return chut.check(name=self.check, digits=digits)
