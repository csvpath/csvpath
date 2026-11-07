import re

from ..util.checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException


class GroupedDigitsDetector:
    """finds fixed-length digit identifiers that are printed in groups and
    have a check digit, e.g. Canada's SIN (3-3-3, Luhn), the UK NHS number
    (3-3-4, mod 11) and Brazil's CPF (###.###.###-##). Each catalog
    detector that uses this class gives its own data:

        length        the number of digits
        layouts       group sizes, e.g. [[3, 3, 3]], separated by a space
                      or a hyphen, one separator throughout (optional)
        formats       printed forms with fixed separators, # for a digit,
                      e.g. "###.###.###-##" (optional)
        check         a ChecksumUtility check name, e.g. "luhn"
        prefixes      the number must start with one of these (optional)
        first_digit_not  digits a number never starts with (optional)
        reject_repeated  true if one digit repeated, e.g. 11111111111,
                      is never valid (optional)
        exclusions    numbers never reported, e.g. published examples

    The digits may always be contiguous too. Numbers must not touch other
    digits."""

    #
    # the catalog data keys this detector reads; a project rulesbase may
    # override these and no others
    #
    CONFIG_KEYS = (
        "length",
        "check",
        "layouts",
        "formats",
        "first_digit_not",
        "prefixes",
        "reject_repeated",
        "exclusions",
    )

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
        formats = config.get("formats") or []
        if not isinstance(formats, list):
            raise MacieException("formats must be a list of printed forms")
        for f in formats:
            if not isinstance(f, str) or f.count("#") != self.length:
                raise MacieException(
                    f"format {f!r} must have {self.length} # for the digits"
                )
            if not any(c != "#" for c in f):
                raise MacieException(
                    f"format {f!r} has no separators; contiguous is always allowed"
                )
            alternatives.insert(
                0, "".join(r"\d" if c == "#" else re.escape(c) for c in f)
            )
        self.candidates = re.compile(
            r"(?<!\d)(?:" + "|".join(alternatives) + r")(?!\d)", re.ASCII
        )
        self.first_digit_not = set(config.get("first_digit_not") or [])
        self.prefixes = config.get("prefixes") or []
        if not isinstance(self.prefixes, list) or not all(
            isinstance(x, str) and x.isdigit() for x in self.prefixes
        ):
            raise MacieException("prefixes must be a list of digit strings")
        self.reject_repeated = config.get("reject_repeated") is True
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
            digits = re.sub(r"\D", "", m.group(0))
            if self.is_valid(digits=digits):
                found.append((m.start(), m.end()))
        return found

    def is_valid(self, *, digits: str) -> bool:
        if digits[0] in self.first_digit_not or digits in self.exclusions:
            return False
        if self.prefixes and not any(digits.startswith(x) for x in self.prefixes):
            return False
        if self.reject_repeated and len(set(digits)) == 1:
            return False
        return chut.check(name=self.check, digits=digits)
