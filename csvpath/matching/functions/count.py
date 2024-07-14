from typing import Any
from csvpath.matching.functions.function import Function


class Count(Function):
    def print(self, msg):
        if self.matcher:
            self.matcher.print(msg)

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if self.value is None:
            if self._function_or_equality:
                self.value = self._get_contained_value(skip=skip)
            else:
                self.value = (
                    self._get_match_count() + 1
                )  # we're eager to +1 because we don't
                # contribute to if there's a match
        return self.value  # or not. we have to act as if.

    def matches(self, *, skip=[]) -> bool:
        return self.value

    def _get_match_count(self) -> int:
        if not self.matcher or not self.matcher.csvpath:
            print("WARNING: no csvpath. are we testing?")
            return -1
        return self.matcher.csvpath.current_match_count()

    def _get_contained_value(self, *, skip=[]) -> Any:
        #
        # need to apply this count function to the contained obj's value
        #
        b = self._function_or_equality.matches(skip=skip)
        if not b:
            return False
        self._id = (
            self.qualifier
            if self.qualifier is not None
            else self.get_id(self._function_or_equality)
        )
        #
        # to_value() is often going to be a bool based on matches().
        # but in a case like: count(now('yyyy-mm-dd')) it would not be
        #
        tracked_value = self._function_or_equality.to_value(skip=skip)
        cnt = self.matcher.get_variable(self._id, tracking=tracked_value, set_if_none=0)
        # print(f"count: cnt: {cnt}, b: {b}, tracked value: {tracked_value}")
        if b:
            cnt += 1
        self.matcher.set_variable(self._id, tracking=tracked_value, value=cnt)
        return cnt
