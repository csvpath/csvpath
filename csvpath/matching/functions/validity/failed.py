# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider
from ..args import Args


class Failed(MatchDecider):
    """matches when the current file is in the failed/invalid state"""

    def check_valid(self) -> None:
        self.description = [
            "Matches when the current file is in the failed/invalid state."
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        if self.name == "failed":
            self.match = not self.matcher.csvpath.is_valid
        elif self.name == "valid":
            self.match = self.matcher.csvpath.is_valid
        else:
            # correct as structure / children exception
            msg = f"Incorrect function name {self.name}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
