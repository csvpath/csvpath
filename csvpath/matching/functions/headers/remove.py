from typing import Any
from csvpath.matching.productions import Equality, Term, Header
from csvpath.matching.util.exceptions import MatchException
from ..function_focus import SideEffect
from ..args import Args


class Remove(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                This function results in the output of collected lines not including the header(s)
                indicated in the argument to remove().
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(name="header identifier", types=[Term], actuals=[int, str])
        a = self.args.argset()
        a.arg(name="header", types=[Header], actuals=[Any])
        sibs = self.siblings()
        self.args.validate(sibs)
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        remove = []
        siblings = self.siblings()
        for s in siblings:
            if isinstance(s, Header):
                s = s.name
            else:
                s = s.to_value(skip=skip)
            remove.append(s)
        rs = []
        for s in remove:
            i = -1
            if isinstance(s, int):
                i = int(s)
            if isinstance(s, str):
                i = self.matcher.header_index(s)
            if i == -1 or i is None:
                msg = f"Unknown header at {i} from {s}"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
            if i in rs:
                # error if we attempt to remove the same header twice. this could
                # happen unintentionally if headers were reset.
                msg = f"Header at {i} already removed"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
            rs.append(i)
        keep = []
        if len(rs) > len(self.matcher.csvpath.headers):
            msg = "Too many headers to remove"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        for i, _ in enumerate(self.matcher.csvpath.headers):
            if i in rs:
                continue
            keep.append(i)
        self.matcher.csvpath.limit_collection_to = keep
        self.match = self.default_match()
