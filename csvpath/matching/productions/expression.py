# pylint: disable=C0114
import traceback
import warnings
from csvpath.util.error import ErrorHandler
from . import Matchable


class Expression(Matchable):
    """root of a match component. the match components are expressions,
    even if we think of them as variables, headers, etc. expressions
    live in a list in the matcher. matcher tracks their activation
    status (True/False) to minimize the number of activations during
    onmatch lookups. expressions' most important job is error
    handling. the expression is responsible for catching and
    handling any error in its descendants.
    """

    def __str__(self) -> str:
        s = ""
        for i, c in enumerate(self.children):
            if i > 0:
                s += ", "
            s = f"{c}"
        return f"""{self._simple_class_name()}(children: {s})"""

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:
            return True
        if self.match is None:
            try:
                ret = True
                for child in self.children:
                    if not child.matches(skip=skip):
                        ret = False
                self.match = ret
            except Exception as e:  # pylint: disable=W0718
                # re: W0718: there may be a better way, but however we
                # do it we have to let nothing through
                e.trace = traceback.format_exc()
                e.source = self
                e.json = self.matcher.to_json(self)
                ErrorHandler(
                    csvpath=self.matcher.csvpath, error_collector=self.matcher.csvpath
                ).handle_error(e)
        return self.match

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def check_valid(self) -> None:
        warnings.filterwarnings("error")
        try:
            super().check_valid()
        except Exception as e:  # pylint: disable=W0718
            # re: W0718: there may be a better way. this case is
            # less clear-cut than the above. still, we probably want
            # to err on the side of over-protecting in case dataops/
            # automation doesn't fully control the csvpaths.
            e.trace = traceback.format_exc()
            e.source = self
            e.message = f"Failed csvpath validity check with: {e}"
            e.json = self.matcher.to_json(self)
            ErrorHandler(
                csvpath=self.matcher.csvpath, error_collector=self.matcher.csvpath
            ).handle_error(e)
            #
            # We always stop if the csvpath itself is found to be invalid
            # before the run starts. The error policy doesn't override that.
            #
            self.matcher.stopped = True
