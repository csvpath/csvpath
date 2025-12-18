# pylint: disable=C0114
from ..function_focus import MatchDecider
from csvpath.matching.functions.lines.dups import FingerPrinter
from csvpath.matching.util.exceptions import MatchException


class Type(MatchDecider):
    @property
    def my_type(self) -> str:
        t = f"{type(self)}".rstrip("'>")
        t = t[t.rfind("'") + 1 :]
        return t

    def _distinct_if(self, skip=None, value=None) -> None:
        if self.distinct:
            name = self.first_non_term_qualifier(self.get_id())
            lines = None
            if value is None:
                sibs = self.siblings()
                sibs = sibs if len(sibs) == 1 else [sibs[0]]
                fingerprint, lines = FingerPrinter._capture_line(
                    self, name, skip=skip, sibs=sibs
                )
            else:
                fingerprint, lines = FingerPrinter._capture_line(
                    self, name, skip=skip, sibs=[value]
                )
            if len(lines) > 1:
                msg = f"Duplicate found on line {self.matcher.csvpath.line_monitor.physical_line_number} where a distict set of values is expected"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
