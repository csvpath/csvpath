# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..args import Args


class Counter(ValueProducer):
    """
    A simple click-counter. every click increments the counter by
    1 unless a child provides an int. effectively the same as doing
    i+=1 in Python or @v = add(@v, 1) in csvpath.
    """

    def check_valid(self) -> None:  # pylint: disable=W0246
        self.args = Args(matchable=self)
        self.args.argset(1).arg(types=[None, Any], actuals=[int])
        self.args.validate(self.siblings())
        name = self.first_non_term_qualifier(self.get_id())
        # initializing the counter to 0. if we don't do this and the counter is
        # never hit (e.g. it is behind a ->) a print returns the counter's name
        # which is confusing.
        self.matcher.get_variable(name, set_if_none=0)
        super().check_valid()  # pylint: disable=W0246

    def _produce_value(self, skip=None) -> None:
        v = self._value_one(skip=skip)
        #
        # if we end up using the id the counter will be hard to identify,
        # probably useless, but better than a name collision on "counter"
        #
        name = self.first_non_term_qualifier(self.get_id())
        counter = self.matcher.get_variable(name, set_if_none=0)
        if v is None:
            counter += 1
        else:
            if not isinstance(v, int):
                v = ExpressionUtility.to_int(v)
            counter += v
        self.matcher.set_variable(name, value=counter)
        self.value = counter

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()  # pragma: no cover
