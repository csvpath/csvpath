# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Reference
import jellyfish


class Metaphone(ValueProducer):
    """if given one arg, returns the metaphone version of the string
    value. if given two args, creates the metaphone version of the
    first arg and expects a reference in the second arg. the
    reference must point to a lookup variable. the lookup variable
    must be in the form: Dict[metaphone,canonical]. the most
    likely way of creating that variable today is to use tally(),
    passing something like: tally(metaphone(#header), #header)"""

    def check_valid(self) -> None:
        self.validate_one_or_two_args(right=[Reference])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        left = self._child_one()
        right = self._child_two()
        vleft = left.to_value(skip=skip)
        vleft = f"{vleft}"
        meta = jellyfish.metaphone(vleft)
        if right is None:
            self.value = meta
        else:
            mappings = right.to_value()
            self.value = mappings.get(meta)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)  # pragma: no cover
        self.match = self._apply_default_match()  # pragma: no cover
