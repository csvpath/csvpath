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
from csvpath.matching.util.exceptions import MatchException


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

    def sibling_values(self, skip=None) -> list:
        #
        # Function validates our args by taking every branch's value before
        # _decide_match runs. as in _decide_match, raising is paused while
        # the branches run: a branch behaves as it would without raise in
        # the policy, and whether its errors stand is decided after all the
        # branches are tried. #760.
        #
        vs = []
        self.matcher.csvpath.pause_raise()
        try:
            for sib in self.siblings():
                try:
                    vs.append(sib.to_value(skip=skip))
                except Exception as e:
                    self.matcher.csvpath.logger.debug(
                        "or() branch %s raised while validating args: %s", sib, e
                    )
                    vs.append(None)
        finally:
            self.matcher.csvpath.resume_raise()
        return vs

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        #
        # in raise mode, or() gives the same result as without raise: a
        # True branch wins, and or() raises only if no branch is True and
        # there were errors (David, 2026-11-19). so raising is paused while
        # the branches run, and or() raises itself below.
        #
        child = self.children[0]
        siblings = child.commas_to_list()
        exceptions = []
        self.matcher.csvpath.pause_raise()
        try:
            for sib in siblings:
                b = False
                try:
                    b = sib.matches(skip=skip)
                #
                # should we only catch MatchException? with raising paused,
                # an exception here is not an error-policy raise.
                #
                except Exception as e:
                    self.matcher.csvpath.logger.debug(
                        "or() branch %s raised: %s", sib, e
                    )
                    exceptions.append(e)
                if b:
                    self.match = True
                    # if we find a True we succeed and dump any errors
                    self.errors = []
                    return
        finally:
            self.matcher.csvpath.resume_raise()
        self.match = False
        #
        # with raising paused, a branch's exception is not an error-policy
        # raise. it may not have been recorded, so add it to the errors.
        #
        for e in exceptions:
            if f"{e}" not in self.errors:
                self.errors.append(f"{e}")
        #
        # if we fail we progress any errors up the stack. remember that
        # we have to become the source for all these messages. that shouldn't
        # be unclear, but regardless.
        #
        for msg in self.errors:
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
        #
        # no branch is True and there were errors: in raise mode we stop the
        # run. one exception is enough; the errors are all recorded above.
        #
        # Expression records the exception again. we make ourselves its
        # source, as we are for the errors just sent, so the ErrorManager
        # drops it as a duplicate. otherwise a parent like not() or an "="
        # becomes the source and the error is recorded twice.
        #
        if self.errors and self.matcher.csvpath.do_i_raise():
            self.my_expression.current_child = self
            if exceptions:
                raise exceptions[0]
            raise MatchException(self.errors[0])
