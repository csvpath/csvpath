# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.exceptions import ChildrenException
from ..function import Function
from ..args import Args


class StartsWith(ValueProducer):
    """checks if a string begins with another string"""

    def check_valid(self) -> None:
        if self.name in ["startswith", "starts_with"]:
            self.aliases = ["startswith", "starts_with"]
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                       Matches when a string begins with another string.
                    """
                ),
            ]
        elif self.name in ["endswith", "ends_with"]:
            self.aliases = ["endswith", "ends_with"]
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                       Matches when a string ends with another string.
                    """
                ),
            ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="check this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="for this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self.children[0].left.to_value(skip=skip)
        if v is None:
            self.value = False
            return
        v = f"{v}".strip()
        sw = self.children[0].right.to_value(skip=skip)
        if sw is None:
            self.value = False
            return
        sw = f"{sw}".strip()
        if sw == "":
            self.value = False
            return

        if self.name in ["startswith", "starts_with"]:
            self.value = v.startswith(sw)
        elif self.name in ["endswith", "ends_with"]:
            self.value = v.endswith(sw)
        else:
            raise ChildrenException(f"Unknown function name: {self.name}")

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)
