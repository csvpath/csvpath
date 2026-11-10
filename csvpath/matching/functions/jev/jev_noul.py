from typesafe_sdk import Noul
from typesafe_sdk import NoulCriteria

from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException
from ..args import Args
from ..function_focus import SideEffect
from .jev_criteria import JevCriteria


class JevNoul(SideEffect):
    def check_valid(self) -> None:  # pragma: no cover
        self.name_qualifier = True
        self.description = [
            "noul() runs a Jev noul query.",
            self.wrap(
                """\
                A noul request returns a probability that the answer to the question provided is "yes".

                noul() runs within a jev(). It cannot be run standalone. Putting a noul() outside a
                jev() results in a built-in CVL error.

                Note that using the jev() function requires adding your Jev account information to
                config.ini under the [jev] section. As always, we strongly recommend keeping your
                credentials in OS environment variables and using ALL_CAPS form variable names in
                config.ini to reference them.
                """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="instructions",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[str],
        )
        a = self.args.argset(2)
        a.arg(
            name="instructions",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[str],
        )
        a.arg(
            name="criteria",
            types=[None, JevCriteria],
            actuals=[NoulCriteria],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        jev = self.parent.parent
        if jev.name != "jev":
            raise ChildrenException(f"Noul cannot be used within {self.parent.name}")

    @property
    def has_internal_variables(self) -> bool:
        return True

    @has_internal_variables.setter
    def has_internal_variables(self, b: bool) -> None: ...

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        sibs = self.siblings()
        inst = sibs[0].to_value(skip=skip)
        crit = sibs[1].to_value(skip=skip) if len(sibs) == 2 else None
        noul = Noul(instructions=inst, criteria=crit)
        self.value = noul

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = True
