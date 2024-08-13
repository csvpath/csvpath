from typing import Any, List
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.expression_utility import ExpressionUtility


class Equality(Matchable):
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
    def left(self):
        return self.children[0]

    @left.setter
    def left(self, o):
        if not self.children:
            self.children = [None, None]
        while len(self.children) < 2:
            self.children.append(None)
        else:
            self.children[0] = o

    @property
    def right(self):
        return self.children[1]

    @right.setter
    def right(self, o):
        if not self.children:
            self.children = [None, None]
        while len(self.children) < 2:
            self.children.append(None)
        self.children[1] = o

    def other_child(self, o):
        if self.left == o:
            return (self.right, 1)
        elif self.right == o:
            return (self.left, 0)
        else:
            return None

    def is_terminal(self, o):
        return (
            isinstance(o, Variable)
            or isinstance(o, Term)
            or isinstance(o, Header)
            or isinstance(o, Function)
            or o is None
        )

    def both_terminal(self):
        return self.is_terminal(self.left) and self.is_terminal(self.right)

    def commas_to_list(self) -> List[Any]:
        ls = []
        self._to_list(ls, self)
        return ls

    def _to_list(self, ls: List, p):
        if isinstance(p, Equality) and p.op == ",":
            self._to_list(ls, p.left)
            self._to_list(ls, p.right)
        else:
            ls.append(p)

    def set_operation(self, op):
        self.op = op

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.left}={self.right}"""

    def _left_nocontrib(self, m) -> bool:
        if isinstance(m, Equality):
            return self._left_nocontrib(m.left)
        else:
            return m.nocontrib

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
    def _do_assignment(self, *, skip=[]) -> bool:
        #
        # the count() function implies onmatch
        #
        count = self.right.name == "count" and len(self.right.children) == 0
        onchange = self.left.onchange
        latch = self.left.latch
        onmatch = self.left.onmatch or count
        asbool = self.left.asbool
        nocontrib = self.left.nocontrib
        noqualifiers = (
            onchange is False
            and latch is False
            and asbool is False
            and nocontrib is False
            and onmatch is False
        )

        ret = True
        #
        # WHAT WE WANT TO SET X TO
        #
        y = self.right.to_value(skip=skip)
        #
        # WE CHECK THE NAME BECAUSE WE MIGHT BE USING A TRACKING VARIABLE
        name = self.left.name
        tracking = self.left.first_non_term_qualifier(None)
        #
        # GET THE CURRENT VALUE, IF ANY
        #
        current_value = self.matcher.get_variable(name, tracking=tracking)

        #
        # SET THE X TO Y IF APPROPRIATE. THE RETURN STARTS AS TRUE.
        #
        if noqualifiers:
            self.matcher.set_variable(name, value=y, tracking=tracking)
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
                    pass
                else:
                    self.matcher.set_variable(name, value=y, tracking=tracking)
                    ret = True
            elif onchange:
                ret = False
            elif latch:
                pass
            else:
                raise Exception("this state should never happen")
        #
        # if onmatch we are True if the line matches,
        # potentially overriding latch and/or onchange,
        # and we set x = y after everything else about the line is done,
        # doing the set in the order all after-match sets are registered,
        # however, if we are onmatch and the line doesn't match
        # we do not set y and we are False.
        # not setting y makes a difference to onchange and latch
        elif onmatch and (latch or onchange):
            if current_value != y:
                if latch and current_value is not None:
                    pass
                else:
                    self.matcher.set_if_all_match(name, value=y, tracking=tracking)
            else:
                pass
            if onchange:
                ret = self.line_matches() and current_value != y
            else:
                ret = self.line_matches()
        #
        # count() is only for matches so implies count.onmatch
        # return set y and return true if the line matches
        # but set y last after everything else about the line is done,
        # doing the set in the order all after-match sets are registered
        elif onmatch:
            ret = self.line_matches()
            if ret:
                #
                # i'm not convinced this delayed set is a good idea but it's not a bad one
                #
                self.matcher.set_if_all_match(name, value=y, tracking=tracking)

        #
        # we don't have any qualifiers that have to do with x = y
        # but we may have asbool or nocontrib
        # so set y and prepare the return to be True
        elif not onmatch and not (latch or onchange):
            self.matcher.set_variable(name, value=y, tracking=tracking)
            ret = True
        else:
            d = {
                "onchange": onchange,
                "latch": latch,
                "onmatch": onmatch,
                "asbool": asbool,
                "nocontrib": nocontrib,
                "noqualifiers": noqualifiers,
                "count": count,
                "y": y,
                "name": name,
                "current_value": current_value,
            }
            raise Exception(
                f"Equality._do_assignment: what case? ret: {ret}, args: {d}"
            )
        #
        # if asbool we apply our interpretation to value of y,
        # if we set y, otherwise we are False,
        # but we can be overridden by nocontrib
        if asbool:
            if ret is True:
                ret = ExpressionUtility.asbool(y)
            else:
                ret = False
        #
        # if nocontrib no matter what we return True because we're
        # removing ourselves from consideration
        if nocontrib:
            ret = True

        return ret

    def _do_when(self, *, skip=[]) -> bool:
        b = None
        if self.op == "->":
            lm = self.left.matches(skip=skip)
            if lm is True:
                b = True
                self.right.matches(skip=skip)
            else:
                if self._left_nocontrib(self.left):
                    b = True
                else:
                    b = False
        else:
            raise ChildrenException("Not a when operation")  # this can't really happen
        return b

    def _do_equality(self, *, skip=[]) -> bool:
        b = None
        left = self.left.to_value(skip=skip)
        right = self.right.to_value(skip=skip)
        if left.__class__ == right.__class__:
            b = self.left.to_value(skip=skip) == self.right.to_value(skip=skip)
        elif (left.__class__ == str and right.__class__ == int) or (
            right.__class__ == str and left.__class__ == int
        ):
            b = f"{left}" == f"{right}"
        else:
            b = f"{left}" == f"{right}"
        return b

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if not self.left or not self.right:
            # this should never happen
            return False
        if not self.match:
            b = None
            if isinstance(self.left, Variable) and self.op == "=":
                b = self._do_assignment(skip=skip)
            elif self.op == "->":
                b = self._do_when(skip=skip)
            else:
                b = self._do_equality(skip=skip)
            self.match = b
        return self.match

    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value
