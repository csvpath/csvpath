from typing import Any, Self, Optional
from ..expression_utility import ExpressionUtility
from enum import Enum


class Qualities(Enum):
    ONMATCH = "onmatch"
    IFEMPTY = "ifempty"
    ONCHANGE = "onchange"
    ASBOOL = "asbool"
    LATCH = "latch"
    NOCONTRIB = "nocontrib"


class Qualified:
    QUALIFIERS = [
        Qualities.ONMATCH.value,
        Qualities.IFEMPTY.value,
        Qualities.ONCHANGE.value,
        Qualities.ASBOOL.value,
        Qualities.NOCONTRIB.value,
        Qualities.LATCH.value,
    ]

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        self.name = name
        if self.name and self.name.__class__ == str:
            self.name = self.name.strip()
        self.qualifier = None
        if name is None:
            self.qualifiers = []
        else:
            n, qs = ExpressionUtility.get_name_and_qualifiers(name)
            self.name = n
            self.qualifiers = qs

    def first_non_term_qualifier(self, default: None) -> Optional[str]:
        if not self.qualifiers:  # this shouldn't happen but what if it did
            return default
        for q in self.qualifiers:
            if q not in Qualified.QUALIFIERS:
                return q
        return default

    def set_qualifiers(self, qs) -> None:
        self.qualifier = qs
        if qs is not None:
            self.qualifiers = qs.split(".")

    def has_onmatch(self) -> bool:
        if self.qualifiers:
            return Qualities.ONMATCH.value in self.qualifiers
        return False

    def has_ifempty(self) -> bool:
        if self.qualifiers:
            return Qualities.IFEMPTY.value in self.qualifiers
        return False

    def has_onchange(self) -> bool:
        if self.qualifiers:
            return Qualities.ONCHANGE.value in self.qualifiers
        return False

    def has_asbool(self) -> bool:
        if self.qualifiers:
            return Qualities.ASBOOL.value in self.qualifiers
        return False

    def has_nocontrib(self) -> bool:
        if self.qualifiers:
            return Qualities.NOCONTRIB.value in self.qualifiers
        return False

    def has_latch(self) -> bool:
        if self.qualifiers:
            return Qualities.LATCH.value in self.qualifiers
        return False

    @property
    def latch(self) -> bool:
        return self.has_latch()

    @property
    def nocontrib(self) -> bool:
        return self.has_nocontrib()

    @property
    def asbool(self) -> bool:
        return self.has_asbool()

    @property
    def onmatch(self) -> bool:
        return self.has_onmatch()

    @property
    def onchange(self) -> bool:
        return self.has_onchange()

    @onchange.setter
    def onchange(self, oc: bool) -> None:
        if Qualities.ONCHANGE.value not in self.qualifiers:
            self.qualifiers.append(Qualities.ONCHANGE.value)
