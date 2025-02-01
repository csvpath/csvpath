# pylint: disable=C0114
import traceback
import warnings
from typing import Any
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from ..util.exceptions import ChildrenException, MatchException
from . import Matchable


class Expression(Matchable, Listener):
    """root of a match component. the match components are expressions,
    even if we think of them as variables, headers, etc. expressions
    live in a list in the matcher. matcher tracks their activation
    status (True/False) to minimize the number of activations during
    onmatch lookups. expressions' most important job is error
    handling. the expression is responsible for catching and
    handling any error in its descendants.
    """

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        Matchable.__init__(self, matcher, name=name, value=value)
        Listener.__init__(self, matcher.csvpath.config)
        self.error_count = 0
        self._index = -1

    #
    # we need to implement the error_listener interface
    # when we get an error over it, we need to just increment
    # the error count. nothing else.
    #
    def metadata_update(self, mdata: Metadata) -> None:
        if mdata.expression_index == self.index:
            self.error_count += 1

    @property
    def index(self) -> int:
        if self._index == -1:
            for i, e in enumerate(self.matcher.expressions):
                if e[0] is self:
                    self._index = i
        return self._index

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
                if not isinstance(e, (ChildrenException, MatchException)):
                    self.matcher.csvpath.error_manager.handle_error(
                        source=self, msg=f"{e}"
                    )
                    self.matcher.csvpath.logger.error(e)
                if self.matcher.csvpath.do_i_raise():
                    raise
        #
        # it is important that the handle_error() calls down-stack already
        # resulted in an update to self.error_count. the way we do
        # threads today that won't be a problem. presumably since order is
        # important in csvpath the grain of async will continue to be
        # more or less the same going forward.
        #
        if self.error_count > 0:
            #
            # if we are matching on errors we want to not just fail lines
            #
            if not self.matcher.csvpath.match_validation_errors:
                self.match = False
        return self.match

    def reset(self) -> None:
        self.value = None
        self.match = None
        self.error_count = 0
        super().reset()

    def check_valid(self) -> None:
        warnings.filterwarnings("error")
        try:
            super().check_valid()
        except Exception as e:  # pylint: disable=W0718
            #
            # we always stop a csvpath that is malformed
            #
            self.matcher.stopped = True
            if not isinstance(e, (ChildrenException, MatchException)):
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=f"{e}")
                self.matcher.csvpath.logger.error(e)
            if self.matcher.csvpath.do_i_raise():
                raise
