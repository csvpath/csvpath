# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer


class HasMatches(ValueProducer):
    """True if there have been matches."""

    def check_valid(self) -> None:  # pylint: disable=W0246
        self.validate_zero_args()
        super().check_valid()  # pylint: disable=W0246

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.value = (
                #
                # do we need to make this _AND aware?
                # I don't think so but watch.
                #
                self.matcher.csvpath.current_match_count
                + 1
            ) > 0
        return self.value

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()  # pragma: no cover
