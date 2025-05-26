# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from csvpath.matching.productions import (
    Term,
    Variable,
    Header,
    Reference,
    Equality,
    Matchable,
)
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function import Function
from ..args import Args


class Or(MatchDecider):
    """does a logical OR of match components"""

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name, child=child)
        self.errors = []

    def reset(self) -> None:
        self.errors = []
        super().reset()

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    or() implements OR logic in a csvpath writer-directed way.

                    Evaluation of or() completes before any errors are handled to
                    allow for the OR operation to be informed by branch invalidity.

                    Remember that logic-mode allows you to apply OR logic to the
                    whole csvpath, if that is needed. or() is of course more
                    specific and composable.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(name="First alternative", types=[Matchable], actuals=[None, Any])
        a.arg(name="Next alternative", types=[Matchable], actuals=[None, Any])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()
        ds = ExpressionUtility.get_my_descendents(self, include_equality=True)
        self.matcher.csvpath.error_manager.veto_callback(sources=ds, callback=self)

    #
    # the "optional" errors problem. or() only shows errors if all its branches fail. but matchables
    # handle their own errors with the error_manager. solution:
    #
    # first catch all MatchExceptions and hold to reraise if every branch fails
    #
    # second get a list of all descendents. pass the list to error_manager for a callback on me.
    # the callback is to handle_error(source, mgs). I collect the messages and resend them to error_manager
    # if all branches fail, as well as raising an exception. setup the veto callback during validation.
    #
    # this keeps all the config between just me and the error_manager
    #
    def handle_error(self, source: Matchable, msg: str) -> None:
        self.errors.append(msg)

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        exceptions = []
        for sib in siblings:
            try:
                b = sib.matches(skip=skip)
            #
            # should we only catch MatchException?
            #
            except Exception as e:
                exceptions.append(e)
            if b:
                self.match = True
                # if we find a True we succeed and dump any errors
                self.errors = []
                return
        self.match = False
        #
        # if we fail we progress any errors up the stack. remember that
        # we have to become the source for all these messages. that shouldn't
        # be unclear, but regardless.
        #
        for msg in self.errors:
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
        #
        # we only get to throw one. is that enough?
        #
        for e in exceptions:
            for e in self.hold:
                raise e
