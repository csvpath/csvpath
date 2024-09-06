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
        noqualifiers = (
            onchange is False
            and latch is False
            and asbool is False
            and nocontrib is False
            and onmatch is False
            #
            # since we're treating notnone as a block on set_variable, rather than
            # as part of the qualifiers decision tree, we don't actually want to
            # acknowledge it here. can still pass it in under its name tho.
            #
            # and notnone is False
        )
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
            "onchange": onchange,
            "latch": latch,
            "onmatch": onmatch,
            "asbool": asbool,
            "nocontrib": nocontrib,
            "notnone": notnone,
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
        # re: R0915,R0912,R0914: definitely too much complexity.
        # but well tested. not time.
        onchange = args["onchange"]
        latch = args["latch"]
        onmatch = args["onmatch"]
        asbool = args["asbool"]
        nocontrib = args["nocontrib"]
        notnone = args["notnone"]
        noqualifiers = args["noqualifiers"]
        y = args["new_value"]
        current_value = args["current_value"]
        line_matches = args[
            "line_matches"
        ]  # if None we'll check in real-time; otherwise, testing
        ret = True
        #
        # SET THE X TO Y IF APPROPRIATE. THE RETURN STARTS AS TRUE.
        #
        if noqualifiers:  # == TEST MARKER 1
            self._set_variable(name, value=y, tracking=tracking, notnone=notnone)
            self.matcher.csvpath.logger.debug("assignment: marker 1")
            ret = True
        #
        # FIND THE RETURN VALUE
        #
        # in the usual case, when we're just talking about x = y,
        # we don't consider the assignment as part of the match
        #
        elif not onmatch and (latch or onchange):
            if current_value != y:
                if latch and current_value is not None:
                    self.matcher.csvpath.logger.debug("assignment: marker 2")
                    pass  # == TEST MARKER 2
                else:
                    self._set_variable(
                        name, value=y, tracking=tracking, notnone=notnone
                    )
                    self.matcher.csvpath.logger.debug("assignment: marker 3 and 4")
                    ret = True  # == TEST MARKER 3  #== TEST MARKER 4
            elif onchange:
                self.matcher.csvpath.logger.debug("assignment: marker 5")
                ret = False  # == TEST MARKER 5
            elif latch:
                self.matcher.csvpath.logger.debug("assignment: marker 6")
                pass  # == TEST MARKER 6
            else:
                s = "Equality:_do_assignment_new_impl:218:"
                s = f"{s} this state is unknown. {ret}, {args}"
                self.matcher.csvpath.logger.error(s)
        #
        # if onmatch we are True if the line matches,
        # potentially overriding latch and/or onchange,
        # and we set x = y after everything else about the line is done,
        # doing the set in the order all after-match sets are registered,
        # however, if we are onmatch and the line doesn't match
        # we do not set y and we are False.
        # not setting y makes a difference to onchange and latch
        elif onmatch and (latch or onchange):  # == TEST MARKER 1
            self.matcher.csvpath.logger.debug("assignment: marker 1 (240)")
            if current_value != y:
                if latch and current_value is not None:
                    self.matcher.csvpath.logger.debug("assignment: marker 7")
                    pass  # == TEST MARKER 7
                else:
                    self.matcher.csvpath.logger.debug("assignment: marker 8, 9, 10")
                    # == TEST MARKER 8  #== TEST MARKER 9 #== TEST MARKER 10
                    #
                    # not none here. and still return ret = True, regardless
                    #
                    if not notnone or y is not None:
                        self.matcher.set_if_all_match(name, value=y, tracking=tracking)
                    ret = True
            else:
                ret = self._test_friendly_line_matches(line_matches)
                # the outcome of onchange only matters if the line matches for onmatch
                if ret and onchange:  # == TEST MARKER 11
                    self.matcher.csvpath.logger.debug("assignment: marker 11")
                    # why are we returning here?
                    return False
                self.matcher.csvpath.logger.debug("assignment: marker 12")
                pass  # == TEST MARKER 12 pylint: disable=W0107
                # re: W0107: the pass is here for clarity
        #
        # count() is only for matches so implies count.onmatch
        # return set y and return true if the line matches
        # but set y last after everything else about the line is done,
        # doing the set in the order all after-match sets are registered
        elif onmatch:
            ret = self._test_friendly_line_matches(line_matches)
            if ret is True:
                #
                # i'm not convinced this delayed set is a good idea but it's not a bad one
                #
                if not notnone or y is not None:
                    self.matcher.set_if_all_match(
                        name, value=y, tracking=tracking
                    )  # == TEST MARKER 13
                    self.matcher.csvpath.logger.debug("assignment: marker 13")
            else:
                self.matcher.csvpath.logger.debug("assignment: marker 14")
                pass  # == TEST MARKER 14
        #
        # we don't have any qualifiers that have to do with x = y
        # but we may have asbool or nocontrib
        # so set y and prepare the return to be True
        elif not onmatch and not (latch or onchange):  # == TEST MARKER 15
            self.matcher.csvpath.logger.debug("assignment: marker 15")
            self._set_variable(name, value=y, tracking=tracking, notnone=notnone)
            ret = True
        else:
            # never happens
            s = "Equality:_do_assignment_new_impl:272:"
            s = f"{s} this state is unknown. {ret}, {args}"
            self.matcher.csvpath.logger.error(s)
        #
        # if asbool we apply our interpretation to value of y,
        # if we set y, otherwise we are False,
        # but we can be overridden by nocontrib
        if asbool:
            if ret is True:  # == TEST MARKER 16 #== TEST MARKER 17
                self.matcher.csvpath.logger.debug("assignment: marker 16, 17")
                ret = ExpressionUtility.asbool(y)
            else:
                self.matcher.csvpath.logger.debug("assignment: marker 16, 17 (305)")
                ret = False
        #
        # if nocontrib no matter what we return True because we're
        # removing ourselves from consideration
        if nocontrib:  # == TEST MARKER 18
            self.matcher.csvpath.logger.debug("assignment: marker 18")
            ret = True
        self.matcher.csvpath.logger.debug(f"done with assignment: ret: {ret}")
        return ret

    def _set_variable(self, name, *, value, tracking=None, notnone=False) -> None:
        if notnone and value is None:
            return
        self.matcher.set_variable(name, value=value, tracking=tracking)

    def _do_when(self, *, skip=None) -> bool:
        b = None
        if self.op == "->":
            lm = self.left.matches(skip=skip)
            if lm is True:
                b = True
                self.right.matches(skip=skip)
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
