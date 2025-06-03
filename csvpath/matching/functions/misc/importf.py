# pylint: disable=C0114
from typing import Any
import traceback
from csvpath.matching.productions import Term, Reference
from csvpath.matching.util.exceptions import MatchComponentException
from csvpath.util.exceptions import InputException
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.expression_encoder import ExpressionEncoder
from ..function_focus import SideEffect
from ..args import Args


class Import(SideEffect):
    """imports one csvpath into another"""

    def __init__(self, matcher, name: str = None, value: Any = None):
        super().__init__(matcher, name=name, child=value)
        self._imported = False

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
            Imports one csvpath into another. The imported csvpath's match
            components are copied into the importing csvpath. Scan instructions are
            not imported.

            Using import() can help with clarity, consistency, efficiency through
            reuse, and testing.

            Import parses both csvpaths, validates both, then puts the two together
            with the imported csvpath running just before where the import function
            was placed. Once the second csvpath has been imported it is as if you
            had written all the match components in the same place.

            Keep in mind that in CsvPath Language, order matters. Import may come
            at any point in a csvpath, allowing you to managed ordering. Remember that
            the onmatch qualifier reorders match components so that those with onmatch
            are evaluted after those without onmatch.

            import() only works in the context of a CsvPaths instance. CsvPaths manages
            finding the imported csvpath. You make the import using a named-paths name,
            optionally with a specific csvpath identity within the named-paths group.

            Named-paths names point to a set of csvpaths. You can point to the csvpath you
            want to import in two ways:

            - Using a reference in the form $named-paths-name.csvpaths.csvpath-identity

            - Giving a named-path name, optionally with a # and the identity of a specific csvpath

            If you plan to import, remember to give your csvpaths an identity in the
            comments using the id or name metadata keys.

            You can import csvpaths from the same named-paths group. That means you could
            even put all your csvpaths in one file and have them import each other as needed.
            When you do this you will still be running the whole named-paths group as a unit.
            Because of that, the csvpaths you import could be run twice. You can prevent that
            by setting the run-mode of the imported csvpaths to no-run.
            """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(name="import this", types=[Term, Reference], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()
        #
        # do not move the inject later in the lifecycle.
        #
        self._inject()

    def to_value(self, *, skip=None) -> Any:
        return self._noop_value()  # pragma: no cover

    def matches(self, *, skip=None) -> bool:
        return self.default_match()  # pragma: no cover

    def _inject(self) -> None:
        # all exceptions are correct structure exceptions.
        # MatchComponent better than Children in this case.
        if self._imported is False:
            if self.matcher.csvpath.csvpaths is None:
                raise MatchComponentException("No CsvPaths instance available")

            name = self._value_one(skip=[self])
            if name is None:
                raise MatchComponentException("Name of import csvpath cannot be None")

            specific = None
            if name.find("#") > -1:
                specific = name[name.find("#") + 1 :]
                name = name[0 : name.find("#")]

            self.matcher.csvpath.logger.info("Starting import from %s", name)
            #
            #
            #
            e = ExpressionUtility.get_my_expression(self)
            if e is None:
                raise MatchComponentException("Cannot find my expression: {self}")
            #
            #
            #
            amatcher = None
            try:
                amatcher = self.matcher.csvpath.parse_named_path(
                    name=name, disposably=True, specific=specific
                )
            except InputException as e:
                self.matcher.csvpath.logger.error(
                    f"Cannot import {name}#{specific}: {e}"
                )
            if (
                amatcher is None
                or not amatcher.expressions
                or len(amatcher.expressions) == 0
            ):
                raise MatchComponentException(
                    f"Inject failed: Could not parse named paths. Named-paths name: {name}. Csvpath name: {specific}."
                )
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
                #
                #
                #
                new_e[0].reset()
                new_e[1] = None
                #
            self.matcher.csvpath.logger.info("Done importing")
            self.matcher.csvpath.logger.debug(
                ExpressionEncoder().valued_list_to_json(self.matcher.expressions)
            )
            self._imported = True
            self.match = self.default_match()
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
