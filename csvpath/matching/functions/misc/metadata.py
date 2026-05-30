# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args
# from csvpath.matching.util.expression_utility import ExpressionUtility
# from csvpath.matching.util.exceptions import MatchException


class Metadata(ValueProducer):
    def check_valid(self) -> None:  # pylint: disable=W0246
        self.description = [
            self.wrap(
                """\
                Provides access to the metadata values and settings directives that are user-set in external comments.

                A metadata key-value pair is set by a word followed by a colon. The value is all characters up to
                the next word-colon key or, if none, the end of the comment.

                The metadata() function finds both mode settings (e.g. xyz-mode:) and any arbitrary key-value pairs
                set by the csvpath writer. Settings directives and user-defined key-values are handled exactly the same.
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
        self.value = self.matcher.csvpath.metadata.get(name)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
