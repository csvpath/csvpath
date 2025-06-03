# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Equality
from csvpath.matching.productions import Variable, Header
from csvpath.matching.util.exceptions import MatchException
from ..function import Function
from ..args import Args


class Tally(SideEffect):
    """collects the number of times values are seen"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                tally() tracks the value of a variable, function, or header.

                It always matches, effectively giving it nocontrib. Tally collects its
                counts regardless of other matches or failures to match, unless you add
                the onmatch qualifier.

                Tally keeps its count in variables named for the values it is tracking.
                It can track multiple values. Each of the values becomes a variable under
                its own name. A header would be tracked under its name, prefixed by tally_,
                as:

                {'tally_firstname': {'Fred':3}}

                Tally also tracks the concatenation of the multiple values under the key
                tally. To use another key name add a non-keyword qualifier to tally. For
                example, tally.birds(#bird_color, #bird_name) has a tally variable of birds
                with values like blue|bluebird,red|redbird.
            """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(name="Value to count", types=[Header, Variable, Function], actuals=[Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        siblings = self.siblings()
        tally = ""
        for _ in siblings:
            tally += f"{_.to_value(skip=skip)}|"
            value = f"{_.to_value(skip=skip)}"
            self._store(_.name, value)
        if len(siblings) > 1:
            self._store(
                "",  # we don't need to pass a name. this data just
                # goes under "tally" or the qualifier
                tally[0 : len(tally) - 1],
            )
        self.value = True

    def _store(self, name, value):
        if name == "":
            name = self.first_non_term_qualifier("tally")
        else:
            name = f"""{self.first_non_term_qualifier("tally")}_{name}"""
        if f"{value}".strip() == "":
            self.matcher.csvpath.logger.warning(
                "Cannot store an empty tracking value in %s. >>%s<<", name, value
            )
            return
        count = self.matcher.get_variable(name, tracking=value)
        if count is None:
            count = 0
        if not isinstance(count, int):
            msg = "Variable {name}"
            if value is not None:
                msg = f"{msg}.{value}"
            msg = f"{msg} must be a number, not {count}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        count += 1
        self.matcher.set_variable(
            name,
            tracking=value,
            value=count,
        )

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)
