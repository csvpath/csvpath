# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Track(SideEffect):
    """uses a match component value to set a tracking
    value, from another match component, on a variable."""

    def check_valid(self) -> None:

        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                track() sets a variable with a tracking value that matches another value.
                The name of the variable is either track or a non-reserved qualifier on
                the function.

                For example:

                     $[*][ track.my_cities(#city, #zip) ]

                This path creates a variable called my_cities. Within that variable each
                city name will track a zip code. This is a dictionary structure. If no
                name qualifier is present the variable name is 'track'.

                Continuing the example, the behind-the-sceens data structure would be
                like:

                     my_cities["Boston"] == 02134

                Track can take the onmatch qualifier. If onmatch is set and the row
                doesn't match track() does not set the tracking variable; however, it does
                still return true. That is to say, track() doesn't have an effect on a row
                matching.
                """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="track under",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        #
        # typically arg two is going to be a string, but it can be anything. there
        # have definitely been cases of int and bool
        #
        a.arg(
            name="tracking value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[Any],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        left = self.children[0].children[0]
        right = self.children[0].children[1]
        varname = self.first_non_term_qualifier(self.name)
        tracking = f"{left.to_value(skip=skip)}".strip()
        v = right.to_value(skip=skip)
        if isinstance(v, str):
            v = f"{v}".strip()
        value = v
        self.matcher.set_variable(varname, tracking=tracking, value=value)
        self.match = self.default_match()
