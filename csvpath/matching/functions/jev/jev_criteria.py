from typesafe_sdk import NoulCriteria

from csvpath.matching.productions import Term
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.exceptions import MatchException
from ..args import Args
from ..function_focus import SideEffect


class JevCriteria(SideEffect):
    def check_valid(self) -> None:  # pragma: no cover
        self.name_qualifier = True
        self.description = [
            "criteria() provides further instructions to a Jev noul.",
            self.wrap(
                """\
                A noul request returns a probability that the answer to the question provided is "yes".

                criteria() is an optional pair of statements, one describing yes, the other no.

                You cannot use a criteria() outside a noul(). For this reason the criteria() is
                considered a side effect.
                """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="Yes means",
            types=[Term],
            actuals=[str],
        )
        a.arg(
            name="No means",
            types=[Term],
            actuals=[str],
        )
        a = self.args.argset()
        a.arg(
            name="Option",
            types=[Term],
            actuals=[str],
        )
        a.arg(
            name="Choice description",
            types=[None, Term, Function],
            actuals=[None, str],
        )

        self.args.validate(self.siblings())
        super().check_valid()

        if self.parent:
            if self.parent.parent.name not in ["noul", "choice", "score"]:
                raise ChildrenException(
                    f"Criteria cannot be used within {self.parent.name}"
                )
        else:
            raise ChildrenException("Parent cannot be None")

    @property
    def has_internal_variables(self) -> bool:
        return True

    @has_internal_variables.setter
    def has_internal_variables(self, b: bool) -> None: ...

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        sibs = self.siblings()

        if self.parent.name == "noul":
            yes = sibs[0]
            no = sibs[1]
            criteria = NoulCriteria(
                true=yes.to_value(skip=skip), false=no.to_value(skip=skip)
            )
            self.value = criteria
        elif self.parent.parent.name in ["score", "choice"]:
            criteria = {}
            k = None
            for s in sibs:
                if k is None:
                    k = s.to_value(skip=skip)
                    continue
                v = s.to_value(skip=skip)
                criteria[k] = v
                k = None
            if k is not None:
                raise MatchException(
                    "Unbalanced criteria. Score and choice criteria have two parts, value and description (description can be none())"
                )
            self.value = criteria

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = True
