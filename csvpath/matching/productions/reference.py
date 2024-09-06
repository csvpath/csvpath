# pylint: disable=C0114
from typing import Any, Dict, List
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..util.exceptions import ChildrenException


class Reference(Matchable):
    """reference is to specific variable values or an existence
    test against a header's values
    """

    def check_valid(self) -> None:  # pylint: disable=W0246
        # re: W0246: Matchable handles this class's children
        super().check_valid()

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        if name is None:
            raise ChildrenException("Name cannot be None")
        if name.strip() == "":
            raise ChildrenException("Name cannot be the empty string")
        #
        # references are in the form:
        #    $file[.path].(variable|header).name[.tracking_name]
        #
        # results are always the most recent. at this time we don't have a way to:
        #   - access results that are not the most recent
        #   - access specific rows
        #   - lookup in header to find another value in the same row
        #
        # some of these may become possible with functions that take references
        #
        self.name_parts = name.split(".")
        self.ref = None

    def __str__(self) -> str:
        return f"""{self.__class__}({self.qualified_name})"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:
            return self._noop_match()
        if self.match is None:
            if self.value is None:
                self.to_value(skip=skip)
            if self.asbool:
                self.match = ExpressionUtility.asbool(self.value)
            else:
                self.match = self.value is not None
        return self.match

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:
            return self._noop_value()
        if self.value is None:
            ref = self._get_reference()
            if ref["var_or_header"] == "headers":
                self.value = self._header_value()
            else:
                self.value = self._variable_value()
        return self.value

    def _get_results(self):
        cs = self.matcher.csvpath.csvpaths
        if cs is None:
            return None
        ref = self._get_reference()
        #
        # our name less the '$' is the name of the named-paths's results
        #
        # the syntax is $named-path.variables-qualifier.varname.tracking
        # the syntax is $named-path.headers-qualifier.headername
        # the syntax is $named-connection.query.queryname.columnname
        #
        results_list = cs.results_manager.get_named_results(ref["file"])
        if results_list and len(results_list) > 0:
            if self.ref["paths_name"] is None:
                results = results_list[0]
            else:
                for r in results_list:
                    if r.paths_name == ref["paths_name"]:
                        results = r
                        break
        return results

    def _get_reference(self) -> Dict[str, str]:
        if self.ref is None:
            self.ref = self._get_reference_for_parts(self.name_parts)
        return self.ref

    def _get_reference_for_parts(self, name_parts: List[str]) -> Dict[str, str]:
        # this method is not persistent to facilitate testing
        # file . variable/header . name . tracking
        # file . path . variable/header . name . tracking
        ref = {}
        if name_parts[1] in ["variables", "headers"]:
            ref["file"] = name_parts[0]
            ref["paths_name"] = None
            ref["var_or_header"] = name_parts[1]
            ref["name"] = name_parts[2]
            ref["tracking"] = name_parts[3] if len(name_parts) == 4 else None
        else:
            ref["file"] = name_parts[0]
            ref["paths_name"] = name_parts[1]
            ref["var_or_header"] = name_parts[2]
            ref["name"] = name_parts[3]
            ref["tracking"] = name_parts[4] if len(name_parts) == 5 else None
        if ref["var_or_header"] not in ["variables", "headers"]:
            raise ChildrenException(
                f"""References must be to variables or headers, not {ref["var_or_header"]}"""
            )
        return ref

    def _variable_value(self) -> Any:
        ref = self._get_reference()
        results = self._get_results()
        csvpath = results.csvpath
        if csvpath is None:
            raise ChildrenException(
                "Results exist but there is no CsvPath that created them"
            )
        return csvpath.get_variable(name=ref["name"], tracking=ref["tracking"])

    def _header_value(self) -> Any:
        """for right now we just need an existence test"""
        results = self._get_results()
        csvpath = results.csvpath
        if csvpath is None:
            raise ChildrenException(
                "Results exist but there is no CsvPath that created them"
            )
        value = False
        ref = self._get_reference()
        #
        # if the csvpath changes the collect columns our headers
        # will not be correct here. leaving that for now.
        # TODO: document the potential gotcha
        #
        print(f"\nReference._header_values: ref: {ref}")
        i = csvpath.header_index(ref["name"])
        print(f"\nReference._header_values: i: {i}")
        if i < 0:
            self.matcher.csvpath.logger.warn(
                f"Index of header {ref['name']} is negative. Check the headers for your reference."
            )
        for line in results.lines:
            if len(line) > i and line[i] is not None and f"{line[i]}".strip() != "":
                value = True
                break
        return value
