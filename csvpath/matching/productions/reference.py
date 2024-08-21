from typing import Any
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from . import ChildrenException


class Reference(Matchable):
    def check_valid(self) -> None:
        super().check_valid()

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        n, qs = ExpressionUtility.get_name_and_qualifiers(name)
        self.name = n
        self.qualifiers = qs
        if n is None:
            raise ChildrenException("Name cannot be None")
        elif n.strip() == "":
            raise ChildrenException("Name cannot be the empty string")

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name}"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return self._noop_match()
        if self.match is None:
            if self.to_value is None:
                self.to_value(skip=skip)
            if self.asbool:
                self.match = ExpressionUtility.asbool(self.value)
            else:
                self.match = self.value is not None
        return self.match

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return self._noop_value()
        if self.value is None:
            results = self._get_results()
            #
            # we have results. now we need to look in headers (the lines by
            # column) or the end-state variables. headers and variables are
            # qualifiers. The specific columns and variables they refer to
            # are treated as non-standard qualifiers.
            #
            if self.headers:
                headname = self.first_non_term_qualifier()
                csvpath = results.csvpath
                if csvpath is None:
                    raise ChildrenException(
                        "Results exist but there is no CsvPath that created them"
                    )
                self.value = False
                i = self._header_index(headname)
                for line in results.lines:
                    if line[i] is not None and f"{line[i]}".strip() != "":
                        self.value = True
                        break
            elif self.variables:
                #
                # the syntax is $named-file[.named-path].variables-qualifier.varname.tracking
                # the syntax is $named-file[.named-path].headers-qualifier.headername
                # the syntax is $named-connection.query.queryname.columnname
                #
                varname = self.first_non_term_qualifier()
                tracking = self.second_non_term_qualifier()
                csvpath = results.csvpath
                if csvpath is None:
                    raise ChildrenException(
                        "Results exist but there is no CsvPath that created them"
                    )
                self.value = csvpath.variables.get_variable(varname, tracking)
            else:
                raise ChildrenException(
                    "References must be to either variables or headers"
                )

            track = self.first_non_term_qualifier(None)
            self.value = self.matcher.get_variable(self.name, tracking=track)
        return self.value

        def _get_results(self):
            cs = self.matcher.csvpath.csvpaths
            if cs is None:
                # can't make the reference
                return None
            #
            # we only check named files results because
            # from a path construction pov we care about the data in files
            #
            # from a validation process pov we may want to reference by what
            # paths generated the results, but today we don't have a syntax for
            # that.
            #
            # our name less the '$' is the name of the named file's results
            #
            results = cs.file_results_manager.get_named_results(self.name)
            if results is None:
                # can't make the reference
                return None
            return results

        def _header_index(self, v):
            if isinstance(v, int) or v.isdigit():
                return int(v)
            else:
                return self.matcher.header_index(v)
