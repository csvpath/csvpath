# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Term
from csvpath.matching.util.exceptions import MatchComponentException
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.expression_encoder import ExpressionEncoder
from ..function_focus import SideEffect


class Import(SideEffect):
    """imports one csvpath into another"""

    def __init__(self, matcher, name: str = None, value: Any = None):
        super().__init__(matcher, name=name, child=value)
        self._imported = False

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term])
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        self._inject()
        return self._noop_value()  # pragma: no cover

    def matches(self, *, skip=None) -> bool:
        self._inject()
        return self._noop_match()  # pragma: no cover

    def _inject(self) -> None:
        if self._imported is False:
            if self.matcher.csvpath.csvpaths is None:
                raise MatchComponentException("No CsvPaths instance available")

            name = self._value_one(skip=[self])
            if name is None:
                raise MatchComponentException("Name of import csvpath cannot be None")

            self.matcher.csvpath.logger.info("Starting import from %s", name)

            e = ExpressionUtility.get_my_expression(self)
            if e is None:
                raise MatchComponentException("Cannot find my expression: {self}")

            amatcher = self.matcher.csvpath.parse_named_path(name=name, disposably=True)
            if (
                amatcher is None
                or not amatcher.expressions
                or len(amatcher.expressions) == 0
            ):
                raise MatchComponentException("Parse named path failed: {name}")
            #
            # find where we do injection of the imported expressions
            #
            insert_at = -1
            pair = None
            for insert_at, pair in enumerate(self.matcher.expressions):
                if pair[0] == e:
                    break
            #
            # do the insert. swap in our matcher, replacing the temp
            # throw-away the import creates.
            #
            self.matcher.csvpath.logger.debug(
                "Import of %s will be at position %s", name, insert_at
            )
            #
            # reverse the list so we end up in the same order
            #
            r = amatcher.expressions[:]
            r.reverse()
            for new_e in r:
                self.matcher.expressions.insert(insert_at, new_e)
                self._set_matcher(new_e[0])
            self.matcher.csvpath.logger.info("Done importing")
            self.matcher.csvpath.logger.debug(
                ExpressionEncoder().valued_list_to_json(self.matcher.expressions)
            )
            self._imported = True
            self.match = self._apply_default_match()
            self.value = self._apply_default_value()

    def _set_matcher(self, e) -> None:
        self.matcher.csvpath.logger.debug(
            "Resetting matcher on imported match components"
        )
        e.matcher = self.matcher
        stacks_of_children = []
        stacks_of_children.append(e.children)
        while len(stacks_of_children) > 0:
            children = stacks_of_children.pop()
            for c in children:
                c.matcher = self.matcher
                stacks_of_children.append(c.children)
