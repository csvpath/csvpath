# pylint: disable=C0114
from ..function_focus import SideEffect
from csvpath.matching.productions.term import Term
from ..args import Args


class PrintLine(SideEffect):
    """prints the current line using a delimiter"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Prints the current line as delimited data.

                    print_line() only prints collected headers. That is, if you use the collect() function
                    to limit the headers you are collecting, print_line() respects that choice.

                    print_line() will output replaced data if print_line() comes after a replace().

                    Use the optional arguments to pass a printouts stream, delimiter and/or quotechar.
                    If a quote char is provided it will be used with every header value, regardless
                    of technical need. At this time print_line() does not attempt to guess delimiters
                    and/or quotechars or use quotechars in a proactive way.

                    Printing to a dedicated printer can help create stand-alone data-ready output. That option
                    is mainly valuable in named-paths group runs where printers' printouts are more clearly
                    separated.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(0)
        a = self.args.argset(3)
        a.arg(name="printer", types=[Term], actuals=[str])
        a.arg(name="delimiter", types=[None, Term], actuals=[str])
        a.arg(name="quotechar", types=[None, Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        printer = self._value_one(skip=skip)
        v = self._value_two(skip=skip)
        if v is None:
            v = ","
        else:
            v = f"{v}".strip()
        delimiter = v
        v = self._value_three(skip=skip)
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
        #
        # we should be able to print to a specific printer. for this function
        # that is important. will need a different signature.
        #
        if printer is not None:
            self.matcher.csvpath.print_to(printer, lineout)
        else:
            self.matcher.csvpath.print(lineout)
        self.match = self.default_match()
