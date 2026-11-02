import re

from ..checksum_utility import ChecksumUtility as chut
from ..macie_exceptions import MacieException
from .iban_detector import IbanDetector


class BankAccountDetector:
    """finds one country's bank account numbers in a cell: IBANs, which
    need no keyword, and the country's Basic Bank Account Numbers (BBANs),
    which do. Our stand-in for Macie's FRANCE_, GERMANY_, ITALY_, SPAIN_
    and UK_BANK_ACCOUNT_NUMBER, which detect both. The parameter is the
    country code, e.g. "bank:GB".

    Each country's BBAN in the catalog:

        shape     one character per position: # a digit, A a letter, C a
                  letter or digit
        layouts   printed groups, e.g. [[4, 4, 4, 4, 4, 3]], separated by
                  a space or a hyphen, one separator throughout
        formats   other printed forms with fixed separators, using the
                  same shape characters, e.g. "##-##-## ########" for a UK
                  sort code and account
        check     "fr_rib_key", "es_bban" or null for none
        domestic_formats  national forms other than the BBAN, with their
                  own shape and no check, e.g. "##-##-## ########" for a
                  UK sort code and account (optional)

    keyword_exempt() tells ManagedIdentifier that IBAN matches need no
    keyword."""

    TAKES_PARAMETER = True
    SHAPES = {"#": r"\d", "A": "[A-Za-z]", "C": "[A-Za-z0-9]"}
    CHECKS = {"fr_rib_key": "fr_rib_key", "es_bban": "es_bban"}

    def __init__(self, *, config: dict, parameter: str | None = None) -> None:
        if not isinstance(config, dict):
            raise TypeError(f"config must be a dict, not {type(config)}")
        lengths = config.get("iban_lengths")
        if not isinstance(lengths, dict):
            raise MacieException("bank needs iban_lengths")
        bbans = config.get("bban")
        if not isinstance(bbans, dict) or parameter not in bbans:
            raise MacieException(
                f"bank needs a country code from its bban table, not {parameter!r}"
            )
        self.country = parameter
        self.iban = IbanDetector(config={"lengths": lengths}, parameter=parameter)
        spec = bbans[parameter]
        shape = spec.get("shape")
        if not isinstance(shape, str) or shape == "" or set(shape) - set(self.SHAPES):
            raise MacieException(f"bban {parameter} shape {shape!r} must use # A C")
        self.shape = shape
        self.check = spec.get("check")
        if self.check is not None and self.check not in self.CHECKS:
            raise MacieException(f"bban {parameter} check {self.check!r} is unknown")
        alternatives = [self._chars(shape)]
        for i, layout in enumerate(spec.get("layouts") or []):
            if (
                not isinstance(layout, list)
                or len(layout) < 2
                or not all(isinstance(g, int) and g > 0 for g in layout)
                or sum(layout) != len(shape)
            ):
                raise MacieException(
                    f"bban {parameter} layout {layout!r} must add up to {len(shape)}"
                )
            alternatives.insert(0, self._grouped(shape=shape, layout=layout, index=i))
        for f in spec.get("formats") or []:
            if (
                not isinstance(f, str)
                or "".join(c for c in f if c in self.SHAPES) != shape
            ):
                raise MacieException(
                    f"bban {parameter} format {f!r} must have the shape {shape}"
                )
            alternatives.insert(
                0,
                "".join(
                    self.SHAPES[c] if c in self.SHAPES else re.escape(c) for c in f
                ),
            )
        self.bban = self._compile(alternatives=alternatives)
        domestic = []
        for f in spec.get("domestic_formats") or []:
            if not isinstance(f, str) or not any(c in self.SHAPES for c in f):
                raise MacieException(f"bban {parameter} domestic format {f!r} is empty")
            domestic.append(
                "".join(self.SHAPES[c] if c in self.SHAPES else re.escape(c) for c in f)
            )
        self.domestic = self._compile(alternatives=domestic) if domestic else None

    @classmethod
    def _compile(cls, *, alternatives: list[str]) -> re.Pattern:
        return re.compile(
            r"(?<![A-Za-z0-9])(?:" + "|".join(alternatives) + r")(?![A-Za-z0-9])",
            re.ASCII,
        )

    def _chars(self, part: str) -> str:
        return "".join(self.SHAPES[c] for c in part)

    def _grouped(self, *, shape: str, layout: list[int], index: int) -> str:
        sep = f"s{index}"
        out = []
        pos = 0
        for n, size in enumerate(layout):
            out.append(self._chars(shape[pos : pos + size]))
            pos += size
            if n == 0:
                out.append(f"(?P<{sep}>[ -])")
            elif n < len(layout) - 1:
                out.append(f"(?P={sep})")
        return "".join(out)

    def matches(self, *, cell: str) -> list[tuple[int, int]]:
        if not isinstance(cell, str):
            raise TypeError(f"cell must be a str, not {type(cell)}")
        found = list(self.iban.matches(cell=cell))
        for m in self.bban.finditer(cell):
            if self._overlaps(found=found, start=m.start(), end=m.end()):
                continue
            if self.is_bban(text=re.sub(r"[ -]", "", m.group(0))):
                found.append((m.start(), m.end()))
        if self.domestic is not None:
            for m in self.domestic.finditer(cell):
                if not self._overlaps(found=found, start=m.start(), end=m.end()):
                    found.append((m.start(), m.end()))
        return sorted(found)

    def is_bban(self, *, text: str) -> bool:
        if len(text) != len(self.shape):
            return False
        if self.check is None:
            return True
        return getattr(chut, self.CHECKS[self.check])(bban=text)

    def keyword_exempt(self, *, cell: str, start: int, end: int) -> bool:
        """True for IBAN matches: only BBANs need a keyword"""
        return (start, end) in self.iban.matches(cell=cell)

    @classmethod
    def _overlaps(cls, *, found: list, start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in found)
