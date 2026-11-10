from typesafe_sdk import Score

from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException
from ..args import Args
from ..function_focus import SideEffect


class JevScore(SideEffect):
    def check_valid(self) -> None:  # pragma: no cover
        self.name_qualifier = True
        self.description = [
            "score() runs a Jev score query.",
            self.wrap(
                """\
                A score request gives the probabilities of items in a list being the best match.
                The answer to a score() is a dict:

                {'type': 'score', 'score': float, 'confidence': float, 'legend': {0: str, 1: str, ...}, 'probabilities': {0: 0..1, 1: 0..1, ...}}


                score() runs within a jev(). It cannot be run standalone. Putting a score() outside a
                jev() results in a built-in CVL error.

                Note that using the jev() function requires adding your Jev account information to
                config.ini under the [jev] section. As always, we strongly recommend keeping your
                credentials in OS environment variables and using ALL_CAPS form variable names in
                config.ini to reference them.
                """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="instructions",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[str],
        )
        a.arg(
            name="criteria",
            types=[Header, Function, Term, Variable, Reference],
            actuals=[None, str],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        jev = self.parent.parent
        if jev.name != "jev":
            raise ChildrenException(f"Score cannot be used within {jev.name}")

    @property
    def has_internal_variables(self) -> bool:
        return True

    @has_internal_variables.setter
    def has_internal_variables(self, b: bool) -> None: ...

    def _produce_value(self, skip=None) -> None:
        inst = self._value_one(skip=skip)
        crit = [s.to_value(skip=skip) for i, s in enumerate(self.siblings()) if i > 0]

        choice = Score(instructions=inst, criteria=crit)
        self.value = choice

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = True
