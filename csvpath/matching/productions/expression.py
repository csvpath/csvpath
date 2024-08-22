from . import DataException, ChildrenException, Matchable
from csvpath.util.error import ErrorHandler
from datetime import datetime
import traceback


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
                e.trace = traceback.format_exc()
                e.source = self
                e.json = self.matcher.to_json(self)
                ErrorHandler(self.matcher.csvpath).handle_error(e)
        return self.match

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()
