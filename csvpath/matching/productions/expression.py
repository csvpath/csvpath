from . import DataException, ChildrenException, Matchable
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
                error = self._new_error(e)
                if self.matcher.csvpath:
                    self.matcher.csvpath.collect_error(error)
                else:
                    print(
                        f"Expression.matches: exception {e} raised. No CsvPath available to handle it."
                    )
        return self.match

    def _new_error(self, ex: Exception) -> Error:
        error = Error()
        error.line_count = (
            self.matcher.csvpath.line_number if self.matcher.csvpath else -1
        )
        error.match_count = (
            self.matcher.csvpath.match_count if self.matcher.csvpath else -1
        )
        error.scan_count = (
            self.matcher.csvpath.scan_count if self.matcher.csvpath else -1
        )
        error.error = ex
        if isinstance(ex, ChildrenException):
            error.json = self.matcher.to_json(self)
        elif isinstance(ex, DataException):
            error.datum = ex.datum if hasattr(ex, "datum") else None
        error.filename = (
            self.matcher.csvpath.scanner.filename
            if self.matcher.csvpath and self.matcher.csvpath.scanner
            else None
        )
        error.at = datetime.now()
        return error

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()
