from ..function_focus import MatchDecider
from ..args import Args


class Validate(MatchDecider):
    def check_valid(self) -> None:
        self.description = [
            "Indicates that a csvpath statement considers a data file valid, regardless of errors. "
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def override_frozen(self) -> bool:
        """fail() and last() must override to return True"""
        return True

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.matcher.csvpath.is_valid = True
        #
        # the default match is approprate because this component
        # is only responsible for registering the fail, it not a
        # reason for it.
        #
        self.match = self.default_match()
