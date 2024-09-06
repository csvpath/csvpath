# pylint: disable=C0114
from csvpath.matching.productions import Term
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer


class End(ValueProducer):
    """returns the value of the last header"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg([Term])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self.matcher.last_header_index()
        if i is None:
            # this could happen when a line is blank or has some other oddity
            pass
        else:
            if len(self.children) > 0:
                v = self.children[0].to_value()
                if isinstance(v, int) or v.isdigit():
                    i = i - int(v)
                else:
                    raise ChildrenException("end()'s term must be a positive int")
            if 0 <= i < len(self.matcher.line):
                self.value = self.matcher.line[i]

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None
