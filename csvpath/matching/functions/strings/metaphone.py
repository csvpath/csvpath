# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Reference, Header, Variable, Term
from ..function import Function
from ..args import Args
from metaphone import doublemetaphone


class Metaphone(ValueProducer):
    """if given one arg, returns the metaphone version of the string
    value. if given two args, creates the metaphone version of the
    first arg and expects a reference in the second arg. the
    reference must point to a lookup variable. the lookup variable
    must be in the form: Dict[metaphone,canonical]. the most
    likely way of creating that variable today is to use track(),
    passing something like: tally(metaphone(#header), #header)"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Function, Header, Variable, Reference], actuals=[str])
        a.arg(types=[None, Reference], actuals=[dict])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        left = self._child_one()
        right = self._child_two()
        vleft = left.to_value(skip=skip)
        vleft = f"{vleft}"
        meta = doublemetaphone(vleft)
        if right is None:
            self.value = meta[0]
        else:
            mappings = right.to_value()
            self.value = mappings.get(meta[0])
            if self.value is None:
                self.value = mappings.get(meta[1])
            if self.value is None:
                # last chance. consider stripping out these characters
                # up-front for all strings.
                vleft = vleft.replace(".", "")
                vleft = vleft.replace(",", "")
                vleft = vleft.replace("/", "")
                vleft = vleft.replace("!", "")
                vleft = vleft.replace("@", "")
                vleft = vleft.replace("-", "")
                vleft = vleft.replace("?", "")
                meta = doublemetaphone(vleft)
                self.value = mappings.get(meta[0])

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)  # pragma: no cover
        self.match = self.default_match()  # pragma: no cover
