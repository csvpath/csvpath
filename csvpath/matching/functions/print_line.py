# pylint: disable=C0114
from typing import Any
from .function import Function


class PrintLine(Function):
    """prints the current line using a delimiter"""

    def check_valid(self) -> None:
        self.validate_zero_one_or_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if self.do_onmatch():
                v = self._value_one(skip=skip)
                if v is None:
                    v = ","
                else:
                    v = f"{v}".strip()
                delimiter = v
                v = self._value_two(skip=skip)
                quoted = ""
                if v is None:
                    pass
                elif v.strip() == "quotes":
                    quoted = '"'
                elif v.strip() == "single":
                    quoted = "'"
                else:
                    pass

                lineout = ""
                use_limit = len(self.matcher.csvpath.limit_collection_to) > 0
                for i, v in enumerate(self.matcher.line):
                    if not use_limit or (
                        use_limit and i in self.matcher.csvpath.limit_collection_to
                    ):
                        d = "" if lineout == "" else delimiter
                        lineout = f"{lineout}{d}{quoted}{v}{quoted}"
                self.matcher.csvpath.print(lineout)

            self.value = True
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = self.to_value(skip=skip)
        return self.match
