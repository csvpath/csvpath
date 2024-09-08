# pylint: disable=C0114
from enum import Enum
import hashlib
from typing import Optional
from ..util.expression_utility import ExpressionUtility
from ..util.exceptions import ChildrenException


class Qualities(Enum):
    """specifies the well-known qualifiers"""

    ONMATCH = "onmatch"
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
    """base class for productions that can have qualifiers"""

    QUALIFIERS = [
        Qualities.ONMATCH.value,
        Qualities.ONCHANGE.value,
        Qualities.ASBOOL.value,
        Qualities.NOCONTRIB.value,
        Qualities.LATCH.value,
        Qualities.VARIABLES.value,
        Qualities.HEADERS.value,
        Qualities.NOTNONE.value,
        Qualities.ONCE.value,
    ]

    def __init__(self, *, name: str = None):
        self.name = name
        # keep the original name so we can look up non-term
        # secondary qualifiers
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

    def first_non_term_qualifier(self, default=None) -> Optional[str]:
        """non-term qualifiers are arbitrary names that may or may not affect
        the operation of the component they are placed on"""
        if not self.qualifiers:  # this shouldn't happen but what if it did
            return default
        for q in self.qualifiers:
            if q not in Qualified.QUALIFIERS:
                return q
        return default

    def second_non_term_qualifier(self, default=None) -> Optional[str]:
        """non-term qualifiers are arbitrary names that may or may not affect
        the operation of the component they are placed on"""
        first = self.first_non_term_qualifier()
        if first is None:
            return default
        for q in self.qualifiers:
            if q == first:
                continue
            if q not in Qualified.QUALIFIERS:
                return q
        return default

    def set_qualifiers(self, qs) -> None:  # pylint: disable=C0116
        self.qualifier = qs
        if qs is not None:
            self.qualifiers = qs.split(".")

    def add_qualifier(self, q) -> None:  # pylint: disable=C0116
        if q not in self.qualifiers:
            self.qualifiers.append(q)

    def has_qualifier(self, q) -> bool:  # pylint: disable=C0116
        return q in self.qualifiers

    def _set(self, string: str, on: bool):
        if on and string not in self.qualifiers:
            self.qualifiers.append(string)
        elif not on:
            try:
                self.qualifiers.remove(string)
            except ValueError:
                pass

    @property
    def variables(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.VARIABLES.value in self.qualifiers
        return False

    @variables.setter
    def variables(self, v: bool) -> None:
        self._set(Qualities.VARIABLES.value, v)

    @property
    def headers(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.HEADERS.value in self.qualifiers
        return False

    @headers.setter
    def headers(self, h: bool) -> None:
        self._set(Qualities.HEADERS.value, h)

    @property
    def notnone(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.NOTNONE.value in self.qualifiers
        return False

    @notnone.setter
    def notnone(self, nn: bool) -> None:
        self._set(Qualities.NOTNONE.value, nn)

    @property
    def latch(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.LATCH.value in self.qualifiers
        return False

    @latch.setter
    def latch(self, latch: bool) -> None:
        self._set(Qualities.LATCH.value, latch)

    @property
    def nocontrib(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.NOCONTRIB.value in self.qualifiers
        return False

    @nocontrib.setter
    def nocontrib(self, nc: bool) -> None:
        self._set(Qualities.NOCONTRIB.value, nc)

    @property
    def asbool(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.ASBOOL.value in self.qualifiers
        return False

    @asbool.setter
    def asbool(self, ab: bool) -> None:
        self._set(Qualities.ASBOOL.value, ab)

    # =============
    # onmatch
    # =============

    @property
    def onmatch(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.ONMATCH.value in self.qualifiers
        return False

    @onmatch.setter
    def onmatch(self, om: bool) -> None:
        self._set(Qualities.ONMATCH.value, om)

    def do_onmatch(self):  # pylint: disable=C0116
        """if True, proceed. True does not mean this
        circumstance obtained, it could just be that this
        qualified doesn't have the qualification."""
        # re: E1101: inheritance structure. good point, but not the time to fix it.
        ret = not self.onmatch or self.line_matches()  # pylint: disable=E1101
        self.matcher.csvpath.logger.debug(  # pylint: disable=E1101
            f"Qualified.do_onmatch: {ret} for {self.name}"
        )
        return ret

    def line_matches(self):
        """checks that all other match components report True. this can result in
        multiple iterations over the match component tree; however, we minimize
        the impact by cutting off at the expression and short-circuiting using the
        self.value and self.match properties. we also take care to not recurse
        by adding self to the skip list."""
        es = self.matcher.expressions  # pylint: disable=E1101
        for e in es:
            m = e[1] is True or e[0].matches(skip=[self])  # pylint: disable=E1101
            if not m:
                return False
        #
        # when we know there's a match we need to propagate it asap
        # in case this or a later onmatched match component wants to use the
        # match count. if we wait for matcher to report to csvpath the count
        # will be hard to explain.
        #
        self.matcher.csvpath.raise_match_count_if()
        return True

    # =============
    # onchange
    # =============

    def do_onchange(self):
        """if True, proceed. True does not mean this
        circumstance obtained, it could just be that this
        qualified doesn't have the qualification."""
        if not self.onchange:
            return True
        _id = self.get_id()  # pylint: disable=E1101
        v = self.matcher.get_variable(_id)  # pylint: disable=E1101
        me = hashlib.sha256(
            f"{self.to_value()}".encode("utf-8")  # pylint: disable=E1101
        ).hexdigest()
        self.matcher.set_variable(_id, value=me)  # pylint: disable=E1101
        return me != v

    @property
    def onchange(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.ONCHANGE.value in self.qualifiers
        return False

    @onchange.setter
    def onchange(self, oc: bool) -> None:
        self._set(Qualities.ONCHANGE.value, oc)

    # =============
    # once
    # =============

    @property
    def once(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.ONCE.value in self.qualifiers
        return False

    @once.setter
    def once(self, o: bool) -> None:
        self._set(Qualities.ONCE.value, o)

    def do_once(self):  # pylint: disable=C0116
        ret = not self.once or self._has_not_yet()
        self.matcher.csvpath.logger.debug(  # pylint: disable=E1101
            f"Qualified.do_ononce: {ret} for {self.name}"
        )
        return ret

    def _has_not_yet(self):
        #
        # supports ONCE
        #
        _id = self.get_id()  # pylint: disable=E1101
        v = self.matcher.get_variable(_id, set_if_none=True)  # pylint: disable=E1101
        return v

    def _set_has_happened(self) -> None:
        #
        # supports ONCE
        #
        _id = self.get_id()  # pylint: disable=E1101
        self.matcher.set_variable(_id, value=False)  # pylint: disable=E1101
        # re: E1101: inheritance structure. good point, but not the time to fix it.
