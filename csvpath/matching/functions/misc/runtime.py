# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args

# from csvpath.matching.util.expression_utility import ExpressionUtility
# from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.runtime_data_collector import RuntimeDataCollector


class Runtime(ValueProducer):
    def check_valid(self) -> None:  # pylint: disable=W0246
        self.description = [
            self.wrap(
                """\
                Provides access to the runtime indicators and config values that
                are serialized to meta.json and available to print().
                """
            ),
        ]
        self.name_qualifier = False
        self.args = Args(matchable=self)
        self.args.argset(1).arg(name="name", types=[None, Any], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()  # pylint: disable=W0246

    def _produce_value(self, skip=None) -> None:
        name = self._value_one(skip=skip)
        if name is None or name.strip() == "":
            return
        r = {}
        RuntimeDataCollector.collect(self.matcher.csvpath, r, True)
        self.value = r.get(name)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
