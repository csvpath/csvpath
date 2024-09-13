# pylint: disable=C0114
from ..function_focus import ValueProducer


class Mismatch(ValueProducer):
    """tests the current headers against an expectation"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        hs = len(self.matcher.csvpath.headers)
        ls = len(self.matcher.line)
        if ls == 1 and f"{self.matcher.line[0]}".strip() == "":
            # blank line with some whitespace chars. we don't take
            # credit for those characters.
            self.value = hs
        else:
            ab = True
            if len(self.children) == 1:
                v = self.children[0].to_value()
                if isinstance(v, str):
                    av = v.strip().lower()
                    if av == "true":
                        ab = True
                    elif av in ["false", "signed"]:
                        ab = False
                else:
                    ab = bool(v)
            if ab:
                self.value = abs(hs - ls)
            else:
                signed = ls - hs
                self.value = signed

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) != 0  # pragma: no cover
        # this has a test
