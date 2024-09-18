# pylint: disable=C0114
from enum import Enum
import hashlib
from typing import List
from typing import Optional
from ..util.expression_utility import ExpressionUtility
from ..util.exceptions import ChildrenException


class Qualities(Enum):
    """specifies the well-known qualifiers"""

    # indicates that the value must go up or the match decision is negative
    INCREASE = "increase"
    # indicates that the value must go down or the match decision is negative
    DECREASE = "decrease"

    # to indicate all other match components must match for the qualified to take effect
    ONMATCH = "onmatch"
    # to indicate that the match decision is only positive when there is a change
    ONCHANGE = "onchange"
    # interpret the to_value as a bool, not an existence test
    ASBOOL = "asbool"
    # indicates that the variable will only be set one time
    LATCH = "latch"
    # to indicate that the match component should return the default, not help decide
    NOCONTRIB = "nocontrib"
    # indicates that the value will not be set unless to a non-none
    NOTNONE = "notnone"
    # indicates that the match component is only activated one time
    ONCE = "once"
    #
    # there is only one function using distinct -- push -- and in an
    # ad hoc kind of way. this token isn't used, but it is reasonable
    # to keep it and formalize the use.
    #
    # indicates that the value being set must be unique in its context
    DISTINCT = "distinct"


class Qualified:
    """base class for productions that can have qualifiers"""

    QUALIFIERS = [
        Qualities.ONMATCH.value,
        Qualities.ONCHANGE.value,
        Qualities.ASBOOL.value,
        Qualities.NOCONTRIB.value,
        Qualities.LATCH.value,
        Qualities.INCREASE.value,
        Qualities.DECREASE.value,
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
        self._qualifiers = []
        # self.qualifiers = []
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

    @property
    def qualifiers(self) -> List[str]:
        return self._qualifiers

    @qualifiers.setter
    def qualifiers(self, qs: list[str]) -> None:
        if qs is None:
            self.matcher.csvpath.logger.warn(
                "Qualifiers set with None. Changing to []."
            )
            qs = []
        self._qualifiers = qs

    def add_qualifier(self, q) -> None:  # pylint: disable=C0116
        if q not in self.qualifiers:
            self.qualifiers.append(q)

    def has_qualifier(self, q) -> bool:  # pylint: disable=C0116
        return q in self.qualifiers

    def has_known_qualifiers(self) -> bool:  # pylint: disable=C0116
        ret = False
        for q in Qualified.QUALIFIERS:
            if q in self.qualifiers:
                ret = True
                break
        return ret

    def _set(self, string: str, on: bool):
        print(f"qualified._set: self quals: {self.qualifiers}")
        if on and string not in self.qualifiers:
            self.qualifiers.append(string)
        elif not on:
            try:
                self.qualifiers.remove(string)
            except ValueError:
                pass

    @property
    def increase(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.INCREASE.value in self.qualifiers
        return False

    @increase.setter
    def increase(self, ii: bool) -> None:
        self._set(Qualities.INCREASE.value, ii)

    @property
    def decrease(self) -> bool:  # pylint: disable=C0116
        if self.qualifiers:
            return Qualities.DECREASE.value in self.qualifiers
        return False

    @decrease.setter
    def decrease(self, dd: bool) -> None:
        self._set(Qualities.DECREASE.value, dd)

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
    # frozen
    # =============

    def do_frozen(self):
        """doing frozen means we execute the code behind the if statement only
        if a) our csvpath.is_frozen() AND b) we are not self.override_frozen().
        if we execute the do_frozen code we can assume we're shutting down.
        perhaps there is some other reason. regardless, do_frozen() is the
        no-op, or the loop continue keyword, that makes us do nothing. fail()
        and last() will override so that they never do_frozen(). everyone else
        (?) will do_frozen() when the freeze is on.
        """
        if self.matcher.csvpath.is_frozen:
            if self.override_frozen():
                self.matcher.csvpath.logger.debug("Overriding frozen in %s", self)
                return False
            self.matcher.csvpath.logger.debug("Not overriding frozen in %s", self)
            return True
        else:
            self.matcher.csvpath.logger.debug("Not overriding frozen in %s", self)
            return False

    def override_frozen(self) -> bool:
        """fail() and last() must override to return True"""
        self.matcher.csvpath.logger.debug(
            "Not overriding frozen in Qualified for %s", self
        )
        return False

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

            m = e[1] is self.default_match() or e[0].matches(
                skip=[self]
            )  # pylint: disable=E1101
            if not m:
                return not self.default_match()
        #
        # when we know there's a match we need to propagate it asap
        # in case this or a later onmatched match component wants to use the
        # match count. if we wait for matcher to report to csvpath the count
        # will be hard to explain.
        #
        self.matcher.csvpath.raise_match_count_if()
        return self.default_match()

    # =============
    # onchange
    # =============

    def do_onchange(self):
        """if True, proceed. True does not mean this
        circumstance obtained, it could just be that this
        qualified doesn't have the qualification."""
        if not self.onchange:
            return True
        _id = f"{self.get_id()}_onchange"  # pylint: disable=E1101
        v = self.matcher.get_variable(_id)  # pylint: disable=E1101
        me = hashlib.sha256(
            f"{self.to_value()}".encode("utf-8")  # pylint: disable=E1101
        ).hexdigest()
        self.matcher.set_variable(_id, value=me)  # pylint: disable=E1101
        # I think this would be better as an is True/is False test
        # but this works fine
        ret = me != v
        # print(f"qualified.do_onchange: v: {v}, me: {me} == {ret}")
        return ret

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
        _id = f"{self.get_id()}_once"  # pylint: disable=E1101
        v = self.matcher.get_variable(_id, set_if_none=True)  # pylint: disable=E1101
        return v

    def _set_has_happened(self) -> None:
        #
        # supports ONCE
        #
        _id = f"{self.get_id()}_once"  # pylint: disable=E1101
        self.matcher.set_variable(_id, value=False)  # pylint: disable=E1101
        # re: E1101: inheritance structure. good point, but not the time to fix it.
