# pylint: disable=C0114
from typing import Any
import traceback
import warnings
from csvpath.util.error import ErrorHandler
from csvpath.matching.util.expression_utility import ExpressionUtility
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

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, name=name, value=value)
        self.errors = []

    def handle_errors_if(self) -> None:
        es = self.errors
        self.errors = []
        for e in es:
            ErrorHandler(
                csvpath=self.matcher.csvpath, error_collector=self.matcher.csvpath
            ).handle_error(e)

    def __str__(self) -> str:
        s = ""
        for i, c in enumerate(self.children):
            if i > 0:
                s += ", "
            s = f"{c}"
        return f"""{self._simple_class_name()}(children: {s})"""

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:
            ret = True  # should be default_match
            self.matching().result(ret).because("skip")
            return ret
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
                #
                # for output ErrorHandler has:
                #   - the print() on the CsvPath
                #   - the error_collector
                #   - the logger on the CsvPath or CsvPaths
                #   - exceptions dumped on system.err
                #
                """
                ErrorHandler(
                    csvpath=self.matcher.csvpath, error_collector=self.matcher.csvpath
                ).handle_error(e)
                """
                self.errors.append(e)
                #
                # if we don't raise the exception we decline the match and
                # continue
                #
                self.match = False
        if len(self.errors) > 0:
            self.match = False
        return self.match

    def reset(self) -> None:
        self.value = None
        self.match = None
        self.errors = []
        super().reset()

    def handle_error(self, error) -> None:
        self.errors.append(error)

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
            """
            ErrorHandler(
                csvpath=self.matcher.csvpath, error_collector=self.matcher.csvpath
            ).handle_error(e)
            """
            self.handle_error(e)
            #
            # We always stop if the csvpath itself is found to be invalid
            # before the run starts. The error policy doesn't override that.
            #
            self.matcher.stopped = True
