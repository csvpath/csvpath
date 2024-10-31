# pylint: disable=C0114
import typing
from csvpath.matching.productions import Equality, Term
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..variables.variables import Variables
from ..function_focus import MatchDecider
from ..headers.headers import Headers
from ..args import Args


class Any(MatchDecider):
    """this class checks various places to find any values present.
    - any()
    - any(header())
    - any(variable())
    - any(Any)
    - any(header(), Any)
    - any(variable(), Any)
    """

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(0)

        a = self.args.argset(2)
        a.arg(types=[Variables, Headers], actuals=[None, typing.Any])
        a.arg(types=[typing.Any], actuals=[None, typing.Any])

        a = self.args.argset(1)
        a.arg(types=[typing.Any, Variables, Headers], actuals=[None, typing.Any])

        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.match = False
        if len(self.children) == 1:
            if isinstance(self.children[0], Equality):
                self.equality()
            elif isinstance(self.children[0], Variables):
                # any(variable())
                self.variable()
            elif isinstance(self.children[0], Headers):
                # any(header())
                self.header()
            else:
                # any(Term) we check in both headers and vars for any matches
                self.check_value()
        else:
            # just any()
            self._bare_any()

    def _bare_any(self) -> None:
        self.match = False
        for h in self.matcher.line:
            if h is None:
                continue
            if f"{h}".strip() == "":
                continue
            self.match = True
            break
        if self.match is False:
            for v in self.matcher.csvpath.variables.values():
                if ExpressionUtility.is_none(v):
                    continue
                self.match = True
                break

    def check_value(self):  # pylint: disable=C0116
        value = self.children[0].to_value()
        for h in self.matcher.line:
            if f"{h}" == f"{value}":
                self.match = True
                break
            if self.match is False:
                for v in self.matcher.csvpath.variables.values():
                    if f"{v}" == f"{value}":
                        self.match = True
                        break

    def header(self):  # pylint: disable=C0116
        for h in self.matcher.line:
            if h is None:
                continue
            if f"{h}".strip() == "":
                continue
            self.match = True
            break

    def variable(self):  # pylint: disable=C0116
        for v in self.matcher.csvpath.variables.values():
            if v is None:
                continue
            if f"{v}".strip() == "":
                continue
            self.match = True
            break

    def equality(self):  # pylint: disable=C0116
        value = self.children[0].right.to_value()
        if isinstance(self.children[0].left, Headers):
            for h in self.matcher.line:
                if f"{h}" == f"{value}":
                    self.match = True
                    break
        elif isinstance(self.children[0].left, Variables):
            for v in self.matcher.csvpath.variables.values():
                if f"{v}" == f"{value}":
                    self.match = True
                    break
        else:
            c = self.children[0].left
            # definitely a structure / children exception
            self.raiseChildrenException(
                f"Left child of any() must be header or variable, not {c}"
            )
