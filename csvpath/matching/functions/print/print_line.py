# pylint: disable=C0114
from ..function_focus import SideEffect
from csvpath.matching.productions.term import Term
from ..args import Args


class PrintLine(SideEffect):
    """prints the current line using a delimiter"""

    def check_valid(self) -> None:
        # self.validate_zero_one_or_two_args()

        args = Args()
        a = args.argset(2)
        a.arg(types=[None, Term], actuals=[None])
        a.arg(types=[None, Term], actuals=[None])
        args.validate(self.siblings())

        super().check_valid()

    def _produce_value(self, skip=None) -> None:
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

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)
