# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Equality, Term, Header
from ..function_focus import SideEffect
from ..args import Args


class Collect(SideEffect):
    """use this class to identify what headers should be collected when
    a line matches. by default all headers are collected."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                When collect() is used only values for the indicated headers
                are returned during the run. If there are four columns in a
                data file and two are collected each line returned by CsvPath.next()
                will contain two values.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(name="header identifier", types=[Term], actuals=[int, str])
        a = self.args.argset()
        a.arg(name="header", types=[Header], actuals=[Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        collect = []
        if isinstance(self.children[0], Equality):
            siblings = self.children[0].commas_to_list()
            for s in siblings:
                if isinstance(s, Header):
                    s = s.name
                else:
                    s = s.to_value(skip=skip)
                collect.append(s)
        else:
            collect.append(self.children[0].to_value(skip=skip))
        cs = []
        for s in collect:
            if isinstance(s, int):
                cs.append(int(s))
            if isinstance(s, str):
                h = self.matcher.header_index(s)
                cs.append(h)
            else:
                # we should be validating for type and actuals so here
                # is not possible, afaik.
                ...
        self.matcher.csvpath.limit_collection_to = cs
        self.match = self.default_match()
