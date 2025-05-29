# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from ..args import Args


class Counter(ValueProducer):
    """
    A simple click-counter. Every click increments the counter by
    1 unless a child provides an int. Effectively the same as doing
    i+=1 in Python or @v = add(@v, 1) in csvpath.
    """

    def check_valid(self) -> None:  # pylint: disable=W0246
        self.description = [
            self.wrap(
                """\
                Increments a variable. The increment is 1 by default.

                Counters must be named using a name qualifier. Without that, the ID generated
                for your counter will be tough to use.

                A name qualifier is an arbitrary name added with a dot after the function
                name and before the parentheses. It looks like counter.my_name()
            """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        self.args.argset(1).arg(
            name="amount to increment by", types=[None, Any], actuals=[int]
        )
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
                v2 = ExpressionUtility.to_int(v)
                if not isinstance(v2, int):
                    #
                    # this should be caught by Args
                    #
                    """
                    msg = f"Cannot convert {v} to an int"
                    self.matcher.csvpath.error_manager.handle_error(
                        source=self, msg=msg
                    )
                    if self.matcher.csvpath.do_i_raise():
                        raise MatchException(msg)
                    """
                    v = v2
            counter += v
        self.matcher.set_variable(name, value=counter)
        self.value = counter

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()  # pragma: no cover
