# pylint: disable=C0114
from ..function_focus import MatchDecider
from csvpath.matching.productions import Term


class Type(MatchDecider):
    def resolve_value(self, skip=None) -> str | None:
        # Args should have already checked Term
        t = self._child_one()
        if isinstance(t, Term):
            name = self._value_one(skip=skip)
            return self.matcher.get_header_value(self, name)
        else:
            # this cannot happen because Args
            self.raiseChildrenException(
                "Error resolving value. This is an internal error."
            )
