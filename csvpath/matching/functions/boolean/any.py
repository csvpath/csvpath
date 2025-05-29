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
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                any() returns True if at least one contained match component
                matches a given value.

                With no arguments any() matches if there are values in any variable or header.

                With a single headers() or variables() function any() returns True if there is
                a match component of the the type indicated with a value.

                With a second argument the test is for the specific value in any match component
                of the indicated type.

                any() is similar to or() or OR logic. While any() gives
                you more fine-grained control, remember that you can
                also use logic-mode to configure a csvpath to use OR as
                the basis for matching.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(0)

        a = self.args.argset(2)
        a.arg(
            name="where to look",
            types=[Variables, Headers],
            actuals=[None, typing.Any],
        )
        a.arg(name="value to find", types=[typing.Any], actuals=[None, typing.Any])

        a = self.args.argset(1)
        a.arg(
            name="where to look",
            types=[typing.Any, Variables, Headers],
            actuals=[None, typing.Any],
        )

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
            msg = f"Left child of any() must be header or variable, not {c}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
