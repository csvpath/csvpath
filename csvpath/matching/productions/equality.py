# pylint: disable=C0114
from typing import Any, List
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.function import Function
from ..util.expression_utility import ExpressionUtility
from ..util.exceptions import ChildrenException


class Equality(Matchable):
    """represents one of:
    1. an equals test;
    2. an assignment;
    3. a when/do;
    4. a comma separated list of arguments
    """

    def __init__(self, matcher):
        super().__init__(matcher)
        self.op: str = (
            "="  # we assume = but if a function or other containing production
        )
        # wants to check we might have a different op

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    @property
    def left(self):  # pylint: disable=C0116
        if len(self.children) > 0:
            return self.children[0]
        return None

    @left.setter
    def left(self, o):
        # note to self: should make sure we are child's parent
        if not self.children:
            self.children = [None, None]
        while len(self.children) < 2:
            self.children.append(None)
        self.children[0] = o

    @property
    def right(self):  # pylint: disable=C0116
        if len(self.children) > 1:
            return self.children[1]
        return None

    @right.setter
    def right(self, o):
        # note to self: should make sure we are child's parent
        if not self.children:
            self.children = [None, None]
        while len(self.children) < 2:
            self.children.append(None)
        self.children[1] = o

    def other_child(self, o):  # pylint: disable=C0116
        if self.left == o:
            return (self.right, 1)
        if self.right == o:
            return (self.left, 0)
        return None

    def is_terminal(self, o):
        """is non equality. a bit misleading because children of functions can be equalities."""
        return isinstance(o, (Variable, Term, Header, Function)) or o is None

    def both_terminal(self):
        """both are non-equalities"""
        return self.is_terminal(self.left) and self.is_terminal(self.right)

    def commas_to_list(self) -> List[Any]:
        """gets the children of op==',' equalities as a list of args"""
        ls = []
        for _ in self.children:
            ls.append(_)
        return ls

    def set_operation(self, op):  # pylint: disable=C0116
        self.op = op

    def __str__(self) -> str:
        if self.op == ",":
            string = ""
            for c in self.children:
                string = f"{c}" if string == "" else f"{string}, {c}"
            return f"""{self._simple_class_name()}({string})"""
        ln = None if self.left is None else f"{self.left}"
        rn = None if self.right is None else f"{self.right}"
        return f"""{ self._simple_class_name() }(left:{ ln } {self.op} right:{rn})"""

    def _left_nocontrib(self, m) -> bool:
        if isinstance(m, Equality):
            return self._left_nocontrib(m.left)
        return m.nocontrib

    def _test_friendly_line_matches(self, matches: bool = None) -> bool:
        if isinstance(matches, bool):
            return matches
        return self.line_matches()

    # ----------------------------------------------
    #
    # these talk about only x = y
    # x = y                                  == True
    # x.latch = y                            == True
    # x.onchange = y                         == True
    #
    # this talks about the row, not x = y
    # x.onmatch = y                          == If match True otherwise False
    #
    # this talks about the value of x
    # x.[anything].asbool = y                == True or False by value of x
    #
    # this talks about the expression x = y and the row
    # x.[anything].nocontrib = y             == True
    #
    # this denormalizing wrapper method exists to facilitate testing.
    # anytime no longer needed it can go.
    #
    def _do_assignment(self, *, skip=None) -> bool:
        #
        # the count() function implies onmatch
        #
        count = self.right.name == "count" and len(self.right.children) == 0
        onchange = self.left.onchange
        latch = self.left.latch
        onmatch = self.left.onmatch or count
        asbool = self.left.asbool
        nocontrib = self.left.nocontrib
        notnone = self.left.notnone
        increase = self.left.increase
        decrease = self.left.decrease
        noqualifiers = self.has_known_qualifiers()
        """
        (
            onchange is False
            and latch is False
            and asbool is False
            and nocontrib is False
            and onmatch is False
            and increase is False
            and decrease is False
            #
            # since we're treating notnone as a block on set_variable, rather than
            # as part of the qualifiers decision tree, we don't actually want to
            # acknowledge it here. can still pass it in under its name tho.
            #
            # and notnone is False
        )
        """
        #
        # WHAT WE WANT TO SET X TO
        #
        y = self.right.to_value(skip=skip)
        self.matcher.csvpath.logger.debug(
            f"pre-assignment: right value: {self.right}: {y}"
        )
        #
        # WE CHECK THE NAME BECAUSE WE MIGHT BE USING A TRACKING VARIABLE
        name = self.left.name
        tracking = self.left.first_non_term_qualifier(None)
        #
        # GET THE CURRENT VALUE, IF ANY
        #
        current_value = self.matcher.get_variable(name, tracking=tracking)
        args = {
            #
            # quals
            #
            "onchange": onchange,
            "latch": latch,
            "onmatch": onmatch,
            "asbool": asbool,
            "nocontrib": nocontrib,
            "notnone": notnone,
            "increase": increase,
            "decrease": decrease,
            #
            # other stuff
            #
            "noqualifiers": noqualifiers,
            "count": count,
            "new_value": y,
            "name": name,
            "tracking": tracking,
            "current_value": current_value,
            "line_matches": None,
        }

        return self._do_assignment_new_impl(name=name, tracking=tracking, args=args)

    def _do_assignment_new_impl(  # pylint: disable=R0915,R0912,R0914
        self, *, name: str, tracking: str = None, args: dict
    ) -> bool:
        # re: R0915,R0912,R0914: refactored.
        #
        # quals
        #
        onchange = args["onchange"]
        latch = args["latch"]
        onmatch = args["onmatch"]
        asbool = args["asbool"]
        nocontrib = args["nocontrib"]
        notnone = args["notnone"]
        increase = args["increase"]
        decrease = args["decrease"]
        #
        # other stuff
        #
        noqualifiers = args["noqualifiers"]
        y = args["new_value"]
        current_value = args["current_value"]
        line_matches = args[
            "line_matches"
        ]  # if None we'll check in real-time; otherwise, testing
        ret = self.default_match()
        #
        # onmatch
        #
        if (
            not onmatch
            or self._test_friendly_line_matches(line_matches) == self.default_match()
        ):
            if latch or onchange:
                ret = self._latch_and_onchange(
                    ret=ret,
                    current_value=current_value,
                    new_value=y,
                    name=name,
                    tracking=tracking,
                    latch=latch,
                    onchange=onchange,
                    notnone=notnone,
                    increase=increase,
                    decrease=decrease,
                )
            else:
                ret = self._set_variable_if(
                    ret,
                    name,
                    current_value=current_value,
                    value=y,
                    tracking=tracking,
                    notnone=notnone,
                    increase=increase,
                    decrease=decrease,
                )
        else:
            ret = not ret

        #
        # asbool
        #
        if asbool:
            if ret is self.default_match():
                self.matcher.csvpath.logger.debug("assignment: marker 16, 17")
                ret = ExpressionUtility.asbool(y)
        #
        # nocontrib
        #
        if nocontrib:
            self.matcher.csvpath.logger.debug("assignment: marker 18")
            ret = self.default_match()
        self.matcher.csvpath.logger.debug(f"done with assignment: ret: {ret}")
        return ret

    def _latch_and_onchange(
        self,
        *,
        ret,
        current_value,
        new_value,
        name,
        tracking,
        latch,
        onchange,
        notnone,
        increase,
        decrease,
    ):
        if current_value != new_value:
            if current_value is None or not latch:
                ret = self.default_match()
                ret = self._set_variable_if(
                    ret,
                    name,
                    current_value=current_value,
                    value=new_value,
                    tracking=tracking,
                    notnone=notnone,
                    increase=increase,
                    decrease=decrease,
                )
        elif onchange:
            ret = not self.default_match()
        return ret

    def _set_variable_if(
        self,
        ret,
        name,
        *,
        current_value,
        value,
        tracking=None,
        notnone=False,
        increase=False,
        decrease=False,
    ) -> bool:
        #
        # not none
        #
        if notnone and value is None:
            return not ret
        #
        # increase and decrease
        #
        if increase and (
            (not current_value and not value)
            or not value
            or (current_value is not None and current_value >= value)
        ):
            self.matcher.csvpath.logger.info(
                "Variable assignment not happening because increase: %s < %s",
                value,
                current_value,
            )
            return not ret
        if decrease and (
            (not current_value and not value)
            or not value
            or (current_value is not None and current_value <= value)
        ):
            self.matcher.csvpath.logger.info(
                "Variable assignment not happening because decrease: %s > %s",
                value,
                current_value,
            )
            return not ret
        #
        # set the value
        #
        self.matcher.set_variable(name, value=value, tracking=tracking)
        return ret

    # ==============================

    def _do_when(self, *, skip=None) -> bool:
        b = None
        if self.op == "->":
            lm = self.left.matches(skip=skip)
            if lm is True:
                b = True
                if self.matcher._AND is False:
                    b = not b
                #
                # adding complication..., but if left is last() we want to unfreeze
                # to let it do what it does. e.g. last() -> print("done!")
                # that opens us to variable changes but even that is probably
                # desirable in this case.
                #
                override = (
                    isinstance(self.left, Function) and self.left.override_frozen()
                )
                if override:
                    self.matcher.csvpath.is_frozen = False
                    self.matcher.csvpath.logger.debug(
                        "Overriding frozen in when/do: %s", self
                    )
                self.right.matches(skip=skip)
                if override:
                    self.matcher.csvpath.logger.debug(
                        "Resetting frozen after when/do: %s", self
                    )
                    self.matcher.csvpath.is_frozen = True
            else:
                b = self._left_nocontrib(self.left)
        else:
            raise ChildrenException("Not a when operation")  # this can't really happen
        return b

    def _do_equality(self, *, skip=None) -> bool:
        b = None
        left = self.left.to_value(skip=skip)
        right = self.right.to_value(skip=skip)
        b = f"{left}".strip() == f"{right}".strip()
        #
        # stringify is probably best most of the time,
        # but it could make "1.0" != "1". there's probably
        # more to do here.
        #
        if not b:
            b = left == right
        return b

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:
            return True
        if not self.left or not self.right:
            # this should never happen
            return False
        if self.match is None:
            b = None
            if isinstance(self.left, Variable) and self.op == "=":
                b = self._do_assignment(skip=skip)
            elif self.op == "->":
                b = self._do_when(skip=skip)
            else:
                b = self._do_equality(skip=skip)
            self.match = b
        return self.match

    def to_value(self, *, skip=None) -> Any:
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value
