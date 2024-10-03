# pylint: disable=C0114
from ..function_focus import MatchDecider
from ..args import Args


class Fail(MatchDecider):
    """this function fails the file that is being processed by setting
    the CsvPath.is_valid attribute to False. Setting that attribute
    fails the CSV being processed by the CsvPath instance since that
    instance is coupled to that file and that one run.
    """

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def override_frozen(self) -> bool:
        """fail() and last() must override to return True"""
        return True

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.matcher.csvpath.is_valid = False
        #
        # the default match is approprate because this component
        # is only responsible for registering the fail, it not a
        # reason for it.
        #
        self.match = self.default_match()


class FailAll(MatchDecider):
    """when called this function fails this CsvPath instance
    and all the CsvPath instances that may be siblings in
    the run
    """

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def override_frozen(self) -> bool:
        """fail() and last() must override to return True"""
        return True

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.matcher.csvpath.is_valid = False
        if self.matcher.csvpath.csvpaths:
            self.matcher.csvpath.csvpaths.fail_all()
        #
        # the default match is approprate because this component
        # is only responsible for registering the fail, it not a
        # reason for it.
        #
        self.match = self.default_match()
