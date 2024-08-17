from .matchable import Matchable
from csvpath.util.error import Error
from datetime import datetime


class Expression(Matchable):
    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if not self.match:
            try:
                ret = True
                for i, child in enumerate(self.children):
                    if not child.matches(skip=skip):
                        ret = False
                self.match = ret
            except Exception as e:
                error = Error()
                error.line = self.matcher.csvpath.line_number
                error.match = self.matcher.csvpath.match_count
                error.scan = self.matcher.csvpath.scan_count
                error.error = e
                error.datum = e.datum
                error.filename = self.matcher.csvpath.scanner.filename
                error.at = datetime.now()
                self.matcher.csvpath.collect_error(error)

        return self.match

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()
