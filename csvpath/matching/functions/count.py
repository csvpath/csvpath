from typing import Any
from csvpath.matching.functions.function import Function

class Count(Function):



    def to_value(self) -> Any:
        self.matcher.print(f"Count: to_value: {self._function_or_equality}: {self._function_or_equality.__class__}")
        if self._function_or_equality:
            return self._get_contained_value()
        else:
            return self._get_match_count() + 1   # we're eager to +1 because we don't
                                                 # contribute to if there's a match
                                                 # or not. we have to act as if.

    def _get_match_count(self) -> int:
        if not self.matcher or not self.matcher.csvpath:
            self.matcher.print("WARNING: no csvpath. are we testing?")
            return -1
        self.matcher.print(f"Count: to_value: {self.matcher.csvpath.current_match_count() + 1}")
        return self.matcher.csvpath.current_match_count()

    def _get_contained_value(self) -> Any:
        #
        # need to apply this count function to the contained obj's value
        #
        self.matcher.print(f"\nCount._get_contained_value: value: {self.value}")
        if not self.value:
            b = self._function_or_equality.matches()
            self.matcher.print(f"Count._get_contained_value: func or equ matches: {b}")
            self._id = self.get_id(self._function_or_equality)
            self.matcher.print(f"Count._get_contained_value: id: {self._id}")
            #
            # to_value() is often going to be a bool based on matches().
            # but in a case like: count(now('yyyy-mm-dd')) it would not be
            #
            tracked_value = self._function_or_equality.to_value()
            self.matcher.print(f"Count._get_contained_value: tracked_value: {tracked_value}")
            cnt = self.matcher.get_variable(self._id, tracking=tracked_value, set_if_none=0)
            self.matcher.print(f"Count._get_contained_value: 1st cnt: {cnt}, b: {b}")
            if b:
                cnt += 1
            self.value = cnt
            self.matcher.print(f"Count._get_contained_value: 2nd cnt: {cnt}")
            self.matcher.set_variable(self._id, tracking=tracked_value, value=self.value)
        return self.value






