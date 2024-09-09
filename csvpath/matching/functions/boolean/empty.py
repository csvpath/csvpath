# pylint: disable=C0114
from ..function_focus import MatchDecider
from csvpath.matching.productions import Header, Variable
from csvpath.matching.util.expression_utility import ExpressionUtility

# note to self: should be possible to request a check of all
# headers.


class Empty(MatchDecider):
    """checks for empty or blank header values in a given line"""

    def check_valid(self) -> None:
        self.validate_one_arg([Header, Variable])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        v = self.children[0].to_value()
        ab = self.children[0].asbool
        if ab:
            v = ExpressionUtility.asbool(v)
            self.match = v
        elif v is None:
            self.match = True
        elif isinstance(v, list) or isinstance(v, tuple):
            if len(v) == 0:
                self.match = True
            else:
                self.match = True
                for _ in v:
                    if _ is not None and not f"{_}".strip() == "":
                        self.match = False
                        break
        elif isinstance(v, dict) and len(dict) == 0:
            # leaving this without checking values because the keys themselves
            # are distinct information, unlike for list and tuple where the
            # indexes are barely information without values.
            self.match = True
        elif isinstance(v, str) and v.strip() == "":
            self.match = True
        else:
            self.match = False
