from uuid import uuid4, UUID
from csvpath.matching.productions import Header, Variable, Reference
from csvpath.matching.functions.function import Function
from ..args import Args
from .type import Type


class Uuid(Type):
    def check_valid(self) -> None:
        self.match_qualifiers.append("notnone")
        self.match_qualifiers.append("distinct")
        self.value_qualifiers.append("notnone")
        self.description = [
            "A line() schema type indicating that the value must be a UUID",
            "As a type, this function will always match empty values unless you use the notnone qualifier.",
        ]
        #
        #
        #
        self.args = Args(matchable=self)
        a = self.args.argset(0)
        a = self.args.argset(1)
        a.arg(
            name="value to check",
            types=[Header, Variable, Reference, Function],
            actuals=[str, None, self.args.EMPTY_STRING],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if self._child_one() is None:
            self.value = uuid4()
        else:
            self.matches(skip=skip)
            self.value = self.match

    def _decide_match(self, skip=None) -> None:
        val = self._value_one(skip=skip)
        self._distinct_if(skip=skip)
        if (val is None or f"{val}".strip() == "") and self.notnone:
            self.match = False
        elif val is None or f"{val}".strip() == "":
            self.match = True
        else:
            self.match = Uuid._is_match(val)

    @classmethod
    def _is_match(cls, value: str) -> bool:
        if value is None:
            return False
        try:
            UUID(value)
            return True
        except ValueError:
            return False
