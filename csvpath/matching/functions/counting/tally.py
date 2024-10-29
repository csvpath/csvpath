# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from csvpath.matching.productions import Equality
from csvpath.matching.productions import Variable, Header
from ..function import Function
from ..args import Args


class Tally(ValueProducer):
    """collects the number of times values are seen"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(types=[Header, Variable, Function], actuals=[Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        siblings = self.siblings()
        tally = ""
        for _ in siblings:
            tally += f"{_.to_value(skip=skip)}|"
            value = f"{_.to_value(skip=skip)}"
            self._store(_.name, value)
        if len(siblings) > 1:
            self._store(
                "",  # we don't need to pass a name. this data just
                # goes under "tally" or the qualifier
                tally[0 : len(tally) - 1],
            )
        self.value = True

    def _store(self, name, value):
        if name == "":
            name = self.first_non_term_qualifier("tally")
        else:
            name = f"""{self.first_non_term_qualifier("tally")}_{name}"""
        if f"{value}".strip() == "":
            self.matcher.csvpath.logger.warning(
                "Cannot store an empty tracking value in %s. >>%s<<", name, value
            )
            return
        count = self.matcher.get_variable(name, tracking=value)
        if count is None:
            count = 0
        count += 1
        self.matcher.set_variable(
            name,
            tracking=value,
            value=count,
        )

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)
