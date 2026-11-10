from typesafe_sdk import Choice

from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException
from ..args import Args
from ..function_focus import SideEffect
from .jev_criteria import JevCriteria


class JevChoice(SideEffect):
    def check_valid(self) -> None:  # pragma: no cover
        self.name_qualifier = True
        self.description = [
            "choice() runs a Jev choice query.",
            self.wrap(
                """\
                A choice request indicates the strongest selection from a list with a confidence score.
                The answer to a choice() is a dict:

                {"type": "choice", "choice": chosen-key, "confidence": 0..1, "probabilities": { key1: 0..1, key2...  } }

                The probability key values sum to exactly 1.

                Your criteria are in pairs, each a key and a description. Alternatively, you may use
                key, none() pairs.

                choice() runs within a jev(). It cannot be run standalone. Putting a choice() outside a
                jev() results in a built-in CVL error.

                Note that using the jev() function requires adding your Jev account information to
                config.ini under the [jev] section. As always, we strongly recommend keeping your
                credentials in OS environment variables and using ALL_CAPS form variable names in
                config.ini to reference them.
                """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="instructions",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[str],
        )
        a.arg(
            name="criteria",
            types=[JevCriteria],
            actuals=[dict],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        jev = self.parent.parent
        if jev.name != "jev":
            raise ChildrenException(f"Choice cannot be used within {jev.name}")

    @property
    def has_internal_variables(self) -> bool:
        return True

    @has_internal_variables.setter
    def has_internal_variables(self, b: bool) -> None: ...

    def _produce_value(self, skip=None) -> None:
        inst = self._value_one(skip=skip)
        crit = self._value_two(skip=skip)

        choice = Choice(instructions=inst, criteria=crit)
        self.value = choice

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = True
