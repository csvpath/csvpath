# pylint: disable=C0114
from csvpath.matching.productions import Equality
from ..function_focus import ValueProducer


class Tally(ValueProducer):
    """collects the number of times values are seen"""

    def check_valid(self) -> None:
        self.validate_one_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = None
        if isinstance(child, Equality):
            siblings = child.commas_to_list()
        else:
            siblings = [child]
        tally = ""
        for _ in siblings:
            tally += f"{_.to_value(skip=skip)}|"
            value = f"{_.to_value(skip=skip)}"
            self._store(_.name, value)
        if len(siblings) > 1:
            self._store(
                self.first_non_term_qualifier("tally"),
                tally[0 : len(tally) - 1],
            )
        self.value = True

    def _store(self, name, value):
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
