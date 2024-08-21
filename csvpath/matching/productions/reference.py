from typing import Any, Dict, List
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from . import ChildrenException


class Reference(Matchable):
    """reference is to specific variable values or an existence
    test against a header's values
    """

    def check_valid(self) -> None:
        super().check_valid()

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        if name is None:
            raise ChildrenException("Name cannot be None")
        elif name.strip() == "":
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
            if self.value is None:
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
            self.ref = self._get_reference()
            if self.ref["variable_or_header"] == "header":
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
        # our name less the '$' is the name of the named file's results
        #
        # the syntax is $named-file[.named-path].variables-qualifier.varname.tracking
        # the syntax is $named-file[.named-path].headers-qualifier.headername
        # the syntax is $named-connection.query.queryname.columnname
        #
        results_list = cs.file_results_manager.get_named_results(ref["file"])
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
        return self._get_reference_for_parts(self.name_parts)

    # TODO: test me
    def _get_reference_for_parts(self, name_parts: List[str]) -> Dict[str, str]:
        # file . variable/header . name . tracking
        # file . path . variable/header . name . tracking
        if self.ref is None:
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
            self.ref = ref
        return self.ref

    def _variable_value(self) -> Any:
        results = self._get_results()
        csvpath = results.csvpath
        if csvpath is None:
            raise ChildrenException(
                "Results exist but there is no CsvPath that created them"
            )
        ref = self._get_reference()
        return csvpath.variables.get_variable(ref["name"], ref["tracking"])

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
        i = csvpath.header_index(ref["var_or_header"])
        for line in results.lines:
            if line[i] is not None and f"{line[i]}".strip() != "":
                value = True
                break
        return value
