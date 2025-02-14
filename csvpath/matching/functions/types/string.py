# pylint: disable=C0114
from csvpath.matching.productions import Header, Variable, Reference, Term
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException

from ..args import Args
from .type import Type


class String(Type):
    def check_valid(self) -> None:
        self.match_qualifiers.append("notnone")
        self.description = [
            "String",
            "string() is used to indicate that a value must be a string to be valid.",
        ]
        #
        #
        #
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(
            name="value",
            types=[Header, Variable, Function, Reference],
            actuals=[str, None, self.args.EMPTY_STRING],
        )
        a.arg(name="max len", types=[None, Term], actuals=[int])
        a.arg(name="min len", types=[None, Term], actuals=[int])
        self.args.validate(self.siblings())
        #
        #
        #
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.matches(skip=skip)
        self.value = f"{self._value_one()}" if self.match else None

    def _decide_match(self, skip=None) -> None:
        value = self._value_one(skip=skip)
        value = f"{value}" if value is not None else None
        val = self._value_one(skip=skip)
        if val is None and self.notnone:
            self.match = False
        elif val is None:
            self.match = True
        else:
            self._check_length_if(val)

    def _check_length_if(self, value, skip=None) -> None:
        maxlen = self._value_two(skip=skip)
        minlen = self._value_three(skip=skip)
        if minlen is None:
            minlen = 0
        if maxlen is None:
            maxlen = len(value)
        if maxlen < minlen:
            #
            # TODO: we could also check this in check_valid(). it is most often
            # going to be two Term ints, not a dynamic value.
            #
            msg = "Max length ({maxlen}) cannot be less than min length ({minlen})"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
        self.match = minlen <= len(value) <= maxlen
