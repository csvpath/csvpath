from typing import Any

from typesafe_sdk import TypeSafeClient

from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.jev.jev_noul import JevNoul
from csvpath.matching.functions.jev.jev_choice import JevChoice
from csvpath.matching.functions.jev.jev_score import JevScore
from csvpath.matching.util.exceptions import ChildrenException
from ..args import Args
from ..function_focus import SideEffect


class Jev(SideEffect):
    def check_valid(self) -> None:  # pragma: no cover
        self.name_qualifier = True
        self.description = [
            self.wrap(
                """\
                jev() creates runs Jev queries to get probability determinations from the Jev
                System One model.

                A jev() function has a context, referred to as "state", and contains one or more
                functions that implement Jev API calls.

                - noul() answers a yes/no question formulated as a yes confirmation. noul()
                results in a float confidence score.

                - choice() classifies an input according to classes provided by the function.
                choice()'s output is a dict.

                - score() returns a score, probability, and confidence against leveled
                options. score()'s output is a dict.

                The jev() operation results in a stack variable containing one item for each query,
                collectively telling you about the state. The individual answers can be
                accessed using the stack variable functions, get() and put(), and jsonpath()

                If you provide a name qualifier the results variable will take that name. For
                example, if your function is jev.myqueries(), the results variable will be named
                myqueries. If you do not provide a name qualifier the results will be available
                under a "jev" variable.

                Note that results are only saved in a variable when you use jev() standalone. If
                you assign jev() to a variable explicitly the function will not create its own
                separate variable.

                Using the jev() function requires adding your Jev account information to config.ini
                in a key named "key" under the [jev] section. As always, we strongly recommend
                keeping your credentials in OS environment variables and using ALL_CAPS form variable
                names in config.ini to reference them.
                """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="state",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[str],
        )
        a.arg(
            name="query",
            types=[JevNoul, JevChoice, JevScore],
            actuals=[None, Any],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        key = self.matcher.csvpath.config.get(section="jev", name="key")
        if key is None:
            raise ChildrenException("Jev key is not available in config.ini")

    @property
    def has_internal_variables(self) -> bool:
        return True

    @has_internal_variables.setter
    def has_internal_variables(self, b: bool) -> None: ...

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        sibs = self.siblings()
        stack = []
        #
        # we have to build and run the jev request here. the individual
        # queries cannot do it for us because we want one parallel request.
        #
        key = self.matcher.csvpath.config.get(section="jev", name="key")
        with TypeSafeClient(model="jev-latest", api_key=key) as client:
            state = sibs[0].to_value(skip=skip)
            qs = {}
            for i, s in enumerate(sibs[1:]):
                qs[str(i)] = s.to_value(skip=skip)
            response = client.system_one(state=state, questions=qs)
            for name in range(0, i + 1):
                answer = response.answers[str(name)]
                if answer.type == "noul":
                    stack.append(answer.noul)
                elif answer.type in ["score", "choice"]:
                    print(f"{answer.model_dump()}")
                    stack.append(answer.model_dump())
            self.value = stack

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = True
        name = self.first_non_term_qualifier("jev")
        self.matcher.csvpath.set_variable(name, value=self.value)
