# pylint: disable=C0114
from csvpath.matching.productions import Header, Variable, Term, Reference
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Get(ValueProducer):
    """returns a variable value, tracking value or stack index"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Returns a variable tracking or index value.

                    A tracking value is similar to a dictionary key, usually keying a
                    count, calculation, or transformation.

                    An index is the 0-based position number of an item in a stack
                    variable. Stack variables are like lists or tuples.

                    While get() and put() make it possible to create and use tracking-value
                    variables in an ad hoc dict-like way, this is not recommended unless there
                    is no simplier solution based on more specific functions.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="var name",
            types=[Header, Term, Function, Variable, Reference],
            actuals=[str, dict],
        )
        a.arg(
            name="tracking value",
            types=[None, Header, Term, Function, Variable],
            actuals=[None, str, int, float, bool, Args.EMPTY_STRING],
        )
        self.args.validate(self.siblings())
        #
        # it might be nice to use name qualifiers to remove one of get()'s
        # arguments but doesn't work that way today.
        #
        # self.name_qualifier = True
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        varname = None
        varname = self._value_one(skip=skip)
        c2 = self._child_two()
        v = None
        if isinstance(varname, dict):
            v = varname
        else:
            v = self.matcher.get_variable(f"{varname}")
        if v is None:
            self.value = None
        elif c2 is None:
            self.value = v
        else:
            t = self._value_two(skip=skip)
            if isinstance(t, int) and (isinstance(v, list) or isinstance(v, tuple)):
                self.value = v[t] if -1 < t < len(v) else None
            elif isinstance(v, dict) and t in v:
                self.value = v[t]
            else:
                self.value = None
                self.matcher.csvpath.logger.warning(
                    f"No way to provide {varname}.{t} given the available variables"
                )

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
