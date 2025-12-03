from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Header, Reference, Variable
from ..function import Function
from ..args import Args


class Insert(SideEffect):
    """inserts a header at an index"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Inserts a new header-value at a certain position within the output data.

                For e.g.: insert(3, @critter)

                This match component creates a new header at index 3 (0-based) and sets the
                value for each line of output to the @critter variable.

            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(name="insert at index", types=[Term], actuals=[int])
        a.arg(name="insert header name", types=[Term], actuals=[str])
        a.arg(
            name="data",
            types=[Variable, Header, Function, Reference],
            actuals=[None, Any],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        index = self._value_one(skip=skip)
        name = self._value_two(skip=skip)
        data = self._value_three(skip=skip)
        #
        # we always use a name. it doesn't need to go into the output data
        # but we need it to exist so that we have a reference telling us if
        # the header exists.
        #
        if self.matcher.header_name(index) != name:
            # find out if we are in the header row
            h = True
            for i, v in enumerate(self.matcher.csvpath.headers):
                if self.matcher.line[i] != v:
                    h = False
            # do the insert
            self.matcher.csvpath.headers.insert(index, name)
            self.matcher.csvpath.logger.debug("Inserted %s at index %s ", name, index)
            # if we're in the header row the data needs the header name
            # otherwise we'll add the value to the data
            if h is True:
                self.matcher.line.insert(index, name)
            else:
                self.matcher.line.insert(index, data)
        else:
            self.matcher.line.insert(index, data)

        self.match = self.default_match()
