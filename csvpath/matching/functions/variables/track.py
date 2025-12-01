# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility as exut

from ..function import Function
from ..args import Args


class Track(SideEffect):
    """uses a match component value to set a tracking
    value, from another match component, on a variable."""

    def check_valid(self) -> None:
        third = "either 'add' or 'collect'" if self.name == "track_any" else "'collect'"
        third2 = (
            "If 'add' is passed, the header values indicated by the second argument are added."
            if self.name == "track_any"
            else ""
        )
        self.description = [
            self._cap_name(),
            self.wrap(
                f"""\
                {self.name}() sets a variable with a tracking value that matches another value.
                The name of the variable is either track or a non-reserved qualifier on
                the function.

                For example:

                     $[*][ {self.name}.my_cities(#city, #zip) ]

                This path creates a variable called my_cities. Within that variable each
                city name will track a zip code. This is a dictionary structure. If no
                name qualifier is present the variable name is 'track'.

                Behind-the-sceens the tracking data structure is like:

                     my_cities["Washington"] == 20521

                {self.name}() can take the onmatch qualifier. If onmatch is set and the row
                doesn't match, {self.name}() does not set the tracking variable

                {self.name}() is a side-effect with no effect on a row matching.

                {self.name}() can take a third argument, {third}. If 'collect' is passed
                the tracked values are pushed on a stack variable. No third argument results
                in the tracked value being replaced at every line.

                {third2}

                Note that track() treats all values as strings; whereas, track_any() attempts
                to convert values. In the zip code example track_any() would not capture
                leading zeros, but track() would.

                """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(3)
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
        name = "'collect' or 'add'" if self.name == "track_any" else "'collect'"
        a.arg(
            name=name,
            types=[None, Term],
            actuals=[Any],
        )
        v = self._value_three(skip=None)
        poss = (
            [None, "collect", "add"] if self.name == "track_any" else [None, "collect"]
        )
        if v not in poss:
            msg = f"If present, the third argument must be {name}, not {v}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        sibs = self.siblings()
        varname = self.first_non_term_qualifier(self.name)
        tracking = f"{sibs[0].to_value(skip=skip)}".strip()
        value = sibs[1].to_value(skip=skip)

        if isinstance(value, str):
            value = value.strip()

        if self.name == "track_any":
            if value != exut.to_simple_bool(value):
                value = exut.to_simple_bool(value)
            elif exut.is_empty(value):
                ...
            elif exut.is_number(value):
                value = float(value)
            elif exut.is_date_or_datetime_str(value):
                #
                # if value is a number we can add it
                # if a datetime we'll add it
                # if it comes back unchanged we'll concat it
                #
                value = exut.to_datetime(value)

        op = sibs[2].to_value(skip=skip) if len(sibs) > 2 else None

        v = self.matcher.get_variable(varname, set_if_none={})
        if tracking not in v:
            v[tracking] = [] if op == "collect" else None
        t = v[tracking]
        if op is None:
            t = value
        elif op == "add":
            if t is None and not exut.is_empty(value):
                t = value
            elif value is None or exut.is_empty(value):
                ...
            else:
                try:
                    t += value
                except Exception as ex:
                    msg = f"Error in add: {ex}"
                    self.matcher.csvpath.error_manager.handle_error(
                        source=self, msg=msg
                    )
                    if self.matcher.csvpath.do_i_raise():
                        raise ChildrenException(msg)
        elif op == "collect":
            if t is None:
                t = []
            if not isinstance(t, list):
                t = [t]
            t.append(value)
        v[tracking] = t
        self.matcher.set_variable(varname, value=v)
        self.match = self.default_match()
