# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Equality


class First(Function):
    """captures the first sighting line number for values"""

    NEVER = -9999999999

    def check_valid(self) -> None:
        self.validate_one_or_more_args()
        super().check_valid()

    def __init__(self, matcher, name: str = None, child: Any = None):
        super().__init__(matcher, child=child, name=name)
        self._my_value_or_none = First.NEVER  # when this var is None we match

    def reset(self) -> None:
        super().reset()
        self._my_value_or_none = First.NEVER

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._my_value_or_none
        if self._my_value_or_none == First.NEVER:
            om = self.has_onmatch()
            if not om or self.line_matches():
                child = self.children[0]
                value = ""
                if isinstance(child, Equality):
                    for _ in child.commas_to_list():
                        value += f"{_.to_value(skip=skip)}"
                else:
                    value = f"{child.to_value(skip=skip)}"
                value = value.strip()
                my_id = self.first_non_term_qualifier(self.name)

                v = self.matcher.get_variable(my_id, tracking=value)
                if v is None:
                    self.matcher.set_variable(
                        my_id,
                        tracking=value,
                        #
                        # we capture line number because the value in knowing it is that
                        # you can go to the file line to inspect it or use it
                        #
                        value=self.matcher.csvpath.line_monitor.physical_line_number,
                    )
                #
                # when we have no earlier value we are first, so we match
                #
                self._my_value_or_none = v
        return self._my_value_or_none

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return True
        om = self.has_onmatch()
        if om and not self.line_matches():
            ret = False
        else:
            #
            # when there is no earlier value we match
            #
            if self._my_value_or_none == First.NEVER:
                self.to_value(skip=skip)
            v = self._my_value_or_none
            ret = v is None
        return ret
