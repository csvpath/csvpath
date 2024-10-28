# pylint: disable=C0114

from typing import Any
from csvpath.matching.productions import Equality
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider
from ..variables.variables import Variables
from ..headers.headers import Headers
from csvpath.matching.productions.variable import Variable
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.header import Header
from ..args import Args


class All(MatchDecider):
    """checks that a number of match components return True"""

    def check_valid(self) -> None:  # pragma: no cover
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.argset(1).arg(types=[None, Variables, Headers], actuals=[])
        self.args.argset().arg(
            types=[None, Function, Variable, Header], actuals=[None, Any]
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        #
        # checking actuals match to arguments definition here.
        # this will go into Matchable.matches()
        #
        # sib_vals = self.sibling_values(skip=skip)
        # self.args.matches(sib_vals)
        #
        #
        #
        self.match = False
        cs = len(self.children)
        if cs == 0:
            # all headers have a value
            self.all_exist()
        if len(self.children) == 1:
            child = self.children[0]
            # a list of headers have values
            if isinstance(child, Equality):
                self.equality()
            elif isinstance(child, Headers):
                self.all_exist()
            elif isinstance(child, Variables):
                self.all_variables()

    def all_variables(self) -> None:  # pylint: disable=C0116
        # default is True in case no vars
        ret = True
        for v in self.matcher.csvpath.variables.values():
            if v is None or f"{v}".strip() == "":
                ret = False
                break
        if self.name == "missing":
            ret = not ret
        self.match = ret

    def all_exist(self):  # pylint: disable=C0116
        ret = True
        if len(self.matcher.line) != len(self.matcher.csvpath.headers):
            ret = False
        if ret is True:
            for h in self.matcher.line:
                if h is None or f"{h}".strip() == "":
                    ret = False
                    break
        if self.name == "missing":
            ret = not ret
        self.match = ret

    def equality(self):  # pylint: disable=C0116
        siblings = self.children[0].commas_to_list()
        ret = True
        for s in siblings:
            v = s.to_value(skip=[self])
            if v is None or f"{v}".strip() == "":
                ret = False
                break
        if self.name == "missing":
            ret = not ret
        self.match = ret
