# pylint: disable=C0114
import hashlib
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer, MatchDecider
from ..args import Args


class Matches(ValueProducer, MatchDecider):
    def check_valid(self) -> None:
        self.name_qualifier = False
        self.description = [
            self.wrap(
                """\
                    Matches if the rest of the line matches.

                    This function is useful in a few less common cases. For example, to achieve
                    a result like:

                        @x.increase.onchange = #0 -> push("top", @x)

                    due to the language's grammar you would actually need to do:

                        @x.increase.onchange = int(#1)
                        matches() -> push("top", @x)
            """
            )
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)

    def _produce_value(self, skip=None) -> None:
        self.value = self.line_matches(increase=False)
