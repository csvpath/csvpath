# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.productions import Term, Variable, Header
from ..function import Function
from ..function_focus import ValueProducer
from ..args import Args


class Int(ValueProducer):
    """attempts to convert a value to an int"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Casts a value to an int.

                    Note that the actuals in the data signatures are types that
                    the value must convert to. A bool True would convert to 1 and
                    would therefore be castable using this function.
                """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="cast this",
            types=[Term, Variable, Header, Function],
            actuals=[None, int, float],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self._value_one(skip=skip)
        if i is None:
            self.value = None
        else:
            self.value = ExpressionUtility.to_int(i)
            if not isinstance(self.value, int):
                msg = f"Cannot convert {i} to int"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()  # pragma: no cover


class Float(ValueProducer):
    """attempts to convert a value to a float"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Term, Variable, Header, Function], actuals=[None, float, int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self._value_one(skip=skip)
        if i is None:
            self.value = None
        else:
            self.value = ExpressionUtility.to_float(i)
            if not isinstance(self.value, float):
                msg = f"Cannot convert {i} to float"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()  # pragma: no cover
