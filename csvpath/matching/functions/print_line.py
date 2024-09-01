from typing import Any
from .function import Function, ChildrenException


class PrintLine(Function):
    def check_valid(self) -> None:
        self.validate_zero_one_or_two_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if self.do_onmatch():
                v = self._value_one()
                if v is None:
                    v = ","
                else:
                    v = f"{v}".strip()
                delimiter = v
                v = self._value_two()
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

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = self.to_value(skip=skip)
        return self.match
