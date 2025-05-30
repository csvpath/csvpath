# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Round(ValueProducer):
    """rounds a number to a certain number of places"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Rounds a number, optionally to a certain number of places.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="round this",
            types=[Term, Variable, Header, Function],
            actuals=[None, bool, str, float, int],
        )
        a.arg(name="to places", types=[None, Term], actuals=[int])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self._value_one(skip=skip)
        places = self._value_two(skip=skip)
        if places is None:
            places = 2

        places2 = ExpressionUtility.to_int(places)
        #
        # TODO: Args should catch conversion error
        #
        if not isinstance(places2, int):
            msg = f"Cannot convert {places} to int"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        #
        # TODO: Args should catch conversion error
        #
        value2 = ExpressionUtility.to_float(value)
        if not isinstance(value2, float):
            msg = f"Cannot convert {value} to float"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)

        self.value = round(value2, places2)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
