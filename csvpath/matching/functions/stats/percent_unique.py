# pylint: disable=C0114
from csvpath.matching.productions import Header
from ..function_focus import ValueProducer
from ..args import Args


class PercentUnique(ValueProducer):
    """return the % of a value that is unique over lines so far seen"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Header], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        tracking = self.children[0].to_value()
        name = self.first_non_term_qualifier("percent_unique")
        v = self.matcher.get_variable(name, tracking=tracking, set_if_none=0)
        v += 1
        self.matcher.set_variable(name, tracking=tracking, value=v)
        d = self.matcher.get_variable(name)
        uniques = 0
        for v, k in enumerate(d):
            if d[k] == 1:
                uniques += 1
        t = self.matcher.csvpath.match_count
        #
        # no longer necessary. match is updated immediately
        # that onmatch -- via line_matches() -- is True
        #
        # t += 1
        self.value = round(uniques / t, 2) * 100

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        self.match = v is not None
