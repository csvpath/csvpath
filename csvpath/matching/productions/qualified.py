from typing import Any, Self, Optional
from ..util.expression_utility import ExpressionUtility
from . import ChildrenException
from enum import Enum


class Qualities(Enum):
    ONMATCH = "onmatch"
    IFEMPTY = "ifempty"
    ONCHANGE = "onchange"
    ASBOOL = "asbool"
    LATCH = "latch"
    NOCONTRIB = "nocontrib"
    VARIABLES = "variables"
    HEADERS = "headers"
    NOTNONE = "notnone"
    ONCE = "once"
    DISTINCT = "distinct"


class Qualified:
    QUALIFIERS = [
        Qualities.ONMATCH.value,
        Qualities.IFEMPTY.value,
        Qualities.ONCHANGE.value,
        Qualities.ASBOOL.value,
        Qualities.NOCONTRIB.value,
        Qualities.LATCH.value,
        Qualities.VARIABLES.value,
        Qualities.HEADERS.value,
        Qualities.NOTNONE.value,
        Qualities.ONCE.value,
    ]

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        self.name = name
        #
        # keep the original name so we can look up non-term secondary qualifiers
        #
        self.qualified_name = name
        if self.name and self.name.__class__ == str:
            self.name = self.name.strip()
        self.qualifier = None
        self.qualifiers = []
        if name is not None:
            n, qs = ExpressionUtility.get_name_and_qualifiers(name)
            self.name = n
            if qs is not None:
                self.qualifiers = qs
        if self.name is not None and self.name.strip() == "":
            raise ChildrenException(f"Name of {self} cannot be the empty string")

    def first_non_term_qualifier(self, default: None) -> Optional[str]:
        if not self.qualifiers:  # this shouldn't happen but what if it did
            return default
        for q in self.qualifiers:
            if q not in Qualified.QUALIFIERS:
                return q
        return default

    def second_non_term_qualifier(self, default: None) -> Optional[str]:
        first = self.first_non_term_qualifier()
        if first is None:
            return default
        for q in self.qualifiers:
            if q == first:
                continue
            elif q not in Qualified.QUALIFIERS:
                return q
        return default

    def set_qualifiers(self, qs) -> None:
        self.qualifier = qs
        if qs is not None:
            self.qualifiers = qs.split(".")

    def add_qualifier(self, q) -> None:
        if q not in self.qualifiers:
            self.qualifiers.append(q)

    def has_qualifier(self, q) -> bool:
        return q in self.qualifiers

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

    def has_once(self) -> bool:
        if self.qualifiers:
            return Qualities.ONCE.value in self.qualifiers
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

    def has_headers(self) -> bool:
        if self.qualifiers:
            return Qualities.HEADERS.value in self.qualifiers
        return False

    def has_variables(self) -> bool:
        if self.qualifiers:
            return Qualities.VARIABLES.value in self.qualifiers
        return False

    def has_notnone(self) -> bool:
        if self.qualifiers:
            return Qualities.NOTNONE.value in self.qualifiers
        return False

    @property
    def latch(self) -> bool:
        return self.has_latch()

    @latch.setter
    def latch(self, b: bool) -> None:
        if Qualities.LATCH.value not in self.qualifiers:
            self.qualifiers.append(Qualities.LATCH.value)

    @property
    def nocontrib(self) -> bool:
        return self.has_nocontrib()

    @nocontrib.setter
    def nocontrib(self, b: bool) -> None:
        if Qualities.NOCONTRIB.value not in self.qualifiers:
            self.qualifiers.append(Qualities.NOCONTRIB.value)

    @property
    def asbool(self) -> bool:
        return self.has_asbool()

    @asbool.setter
    def asbool(self, b: bool) -> None:
        if Qualities.ASBOOL.value not in self.qualifiers:
            self.qualifiers.append(Qualities.ASBOOL.value)

    @property
    def once(self) -> bool:
        return self.has_once()

    @once.setter
    def once(self, b: bool) -> None:
        if Qualities.ONCE.value not in self.qualifiers:
            self.qualifiers.append(Qualities.ONCE.value)

    @property
    def onmatch(self) -> bool:
        return self.has_onmatch()

    @onmatch.setter
    def onmatch(self, b: bool) -> None:
        if Qualities.ONMATCH.value not in self.qualifiers:
            self.qualifiers.append(Qualities.ONMATCH.value)

    @property
    def onchange(self) -> bool:
        return self.has_onchange()

    @onchange.setter
    def onchange(self, oc: bool) -> None:
        if Qualities.ONCHANGE.value not in self.qualifiers:
            self.qualifiers.append(Qualities.ONCHANGE.value)

    @property
    def variables(self) -> bool:
        return self.has_variables()

    @variables.setter
    def variables(self, oc: bool) -> None:
        if Qualities.VARIABLES.value not in self.qualifiers:
            self.qualifiers.append(Qualities.VARIABLES.value)

    @property
    def headers(self) -> bool:
        return self.has_headers()

    @headers.setter
    def headers(self, oc: bool) -> None:
        if Qualities.HEADERS.value not in self.qualifiers:
            self.qualifiers.append(Qualities.HEADERS.value)

    @property
    def notnone(self) -> bool:
        return self.has_notnone()

    @notnone.setter
    def notnone(self, nn: bool) -> None:
        if Qualities.NOTNONE.value not in self.qualifiers:
            self.qualifiers.append(Qualities.NOTNONE.value)
