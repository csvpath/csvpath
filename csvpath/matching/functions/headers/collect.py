# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Equality, Term
from ..function_focus import SideEffect
from ..args import Args


class Collect(SideEffect):
    """use this class to identify what headers should be collected when
    a line matches. by default all headers are collected."""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(types=[Term], actuals=[int, str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        collect = []
        if isinstance(self.children[0], Equality):
            siblings = self.children[0].commas_to_list()
            for s in siblings:
                collect.append(s.to_value(skip=skip))
        else:
            collect.append(self.children[0].to_value(skip=skip))
        cs = []
        for s in collect:
            if not isinstance(s, int):
                cs.append(self.matcher.header_index(s))
            else:
                cs.append(int(s))
        # print(f"collect.dec_mat: cs: {cs}")
        self.matcher.csvpath.limit_collection_to = cs
        self.match = self.default_match()
