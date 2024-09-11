# pylint: disable=C0114
from typing import Any, Dict, List
from csvpath.matching.productions.matchable import Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..util.exceptions import ChildrenException, MatchException, DataException


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
            raise ChildrenException("Name cannot be None")  # pragma: no cover
        if name.strip() == "":
            raise ChildrenException(
                "Name cannot be the empty string"
            )  # pragma: no cover
        #
        # references are in the form:
        #    $file[.path/name].(csvpath|metadata|variable|header).name[.tracking_name/index]
        #
        # results are always the most recent unless we pull specific results for a
        # header ref using a tracking value against an "id" or "name" metadata
        # field on the target csvpath. in that case the results might not be the
        # most recent, if the metadata name/id changes.
        #
        # at this time we don't have a more precise way to:
        #   - access results that are not the most recent
        #   - access specific rows
        #   - lookup in header to find another value in the same row
        #
        # some or all of these may become possible with functions that take
        # references
        #
        self.name_parts = name.split(".")
        self.ref = None
        self._cache_vars = None
        self._cache_headers = None
        if self.matcher:
            # it is possible unit tests might not give us a matcher
            # don't know any other reason. doesn't hurt to check tho.
            self.matcher._cache_me(self)

    def clear_caches(self) -> None:
        self._cache_vars = None
        self._cache_headers = None

    def __str__(self) -> str:  # pragma: no cover
        return f"""{self.__class__}({self.qualified_name})"""

    def reset(self) -> None:
        self.value = None
        self.match = None  # pragma: no cover
        super().reset()

    def matches(self, *, skip=None) -> bool:  # pragma: no cover
        if skip and self in skip:
            return self._noop_match()  # pragma: no cover
        if self.match is None:
            if self.value is None:
                self.to_value(skip=skip)
                """
                #
                # references cannot take qualifiers
                #
                if self.asbool:
                    self.match = ExpressionUtility.asbool(self.value) # pragma: no cover
                """
            # else:
            self.match = self.value is not None
            print(
                f"\nReference.matches: self.match: {self.match}, self.value: {self.value}\n"
            )
        return self.match  # pragma: no cover

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:
            return self._noop_value()  # pragma: no cover
        if self.value is None:
            self.matcher.csvpath.logger.info(
                "Beginning a lookup on %s", self
            )  # pragma: no cover
            ref = self._get_reference()
            if ref["var_or_header"] == "headers":
                if self._cache_vars is not None:
                    self.value = self._cache_headers
                else:
                    self.value = self._header_value()
                    self._cache_headers = self.value
            else:
                if self._cache_vars is not None:
                    self.value = self._cache_vars
                else:
                    self.value = self._variable_value()
                    self._cache_vars = self.value
        return self.value

    def _get_results(self):
        cs = self.matcher.csvpath.csvpaths
        if cs is None:
            self.matcher.csvpath.logger.error(
                "Attemped to make a reference %s without a CsvPaths instance available",
                self,
            )
            raise MatchException(
                "References cannot be used without a CsvPaths instance"
            )
        ref = self._get_reference()
        #
        # our name less the '$' is the name of the named-paths's results
        #
        # the syntax is $named-path.variables-qualifier.varname.tracking
        # the syntax is $named-path.headers-qualifier.headername
        # the syntax is $named-connection.query.queryname.columnname
        #
        results_list = cs.results_manager.get_named_results(ref["paths_name"])
        if results_list and len(results_list) > 0:
            # if self.ref["paths_name"] is None:
            results = results_list[0]
            # else:
            #    for r in results_list:
            # this is a legacy that should be removed when time.
            # we should have paths_name on every result, so always
            # the 1st one. with headers we use the tracking value
            # to identify a specific csvpath.
            #        if r.paths_name == ref["paths_name"]:
            #            results = r
            #            break
        elif results_list:
            # the results exist but are empty. when would this happen?
            self.matcher.csvpath.logger.error(
                "Unknown state: results for %s came back empty", self
            )
        else:
            #
            # this is almost certainly a user misconfiguration
            #
            raise MatchException("Results cannot be None for reference %s", self)
        return results

    def _get_reference(self) -> Dict[str, str]:
        if self.ref is None:
            self.ref = self._get_reference_for_parts(self.name_parts)
        return self.ref

    def _get_reference_for_parts(self, name_parts: List[str]) -> Dict[str, str]:
        ref = {}
        if name_parts[1] in ["variables", "headers"]:
            ref["paths_name"] = name_parts[0]
            ref["var_or_header"] = name_parts[1]
            ref["name"] = name_parts[2]
            ref["tracking"] = name_parts[3] if len(name_parts) == 4 else None
        # the next few lines are harmless but dead. they likely will come back. atm
        # they trigger coverage
        else:
            ref["paths_name"] = name_parts[0]
            ref["var_or_header"] = name_parts[1]
            ref["name"] = name_parts[2]
            ref["tracking"] = name_parts[3] if len(name_parts) == 4 else None
        #
        # assuming we're cutting this off here because we don't yet support
        # metadata and csvpaths in plain references yet. we do support
        # them in print references.
        #
        if ref["var_or_header"] not in ["variables", "headers"]:
            raise ChildrenException(
                f"""References must be to variables or headers, not {ref["var_or_header"]}"""
            )
        return ref

    def _variable_value(self) -> Any:
        ref = self._get_reference()
        cs = self.matcher.csvpath.csvpaths  # pragma: no cover
        if cs is None:
            raise MatchException(
                "References cannot be used without a CsvPaths instance"
            )
        vs = cs.results_manager.get_variables(ref["paths_name"])
        ret = None
        if ref["name"] in vs:
            v = vs[ref["name"]]
            if ref["tracking"] and ref["tracking"] in v:
                ret = v[ref["tracking"]]
            elif ref["tracking"]:
                ret = None
            else:
                ret = v
        else:
            raise DataException("Results exist but the variable is unknown: %s", self)
        return ret

    def _header_value(self) -> Any:
        ref = self._get_reference()
        name = ref["paths_name"]
        rm = self.matcher.csvpath.csvpaths.results_manager
        ret = None
        if rm.has_lines(name):
            #
            # we pull data. if we have a tracking value we can pull a specific csvpath's result
            #
            if rm.get_number_of_results(name) == 1:
                rs = rm.get_named_results(name)
                ret = self._get_value_from_results(ref, rs[0])
            elif ref["tracking"]:
                #
                # find the specific path if we have a tracking value.
                # tested in test_reference_specific_header_lookup. manager has 100% coverage.
                #
                r = rm.get_specific_named_result(
                    name, ref["tracking"]
                )  # pragma: no cover
                if r is None:
                    raise MatchException(
                        "No results in %s for metadata id or name %s in %s",
                        name,
                        ref["tracking"],
                        self,
                    )
                ret = self._get_value_from_results(ref, r)
            else:
                #
                # are we really going to aggregate all the values from all the
                # csvpaths here? that would likely be too expensive in a large
                # fraction of cases.
                #
                raise MatchException(
                    """Too many results. At this time references must be to a
                    single path. A named-paths with just one path or a path which is
                    identified by a metadata id or name matched to a tracking value
                    in the reference"""
                )
        else:
            raise MatchException("Results may exist but no data was captured")
        return ret

    def _get_value_from_results(self, ref, result):
        csvpath = result.csvpath
        i = csvpath.header_index(ref["name"])
        if i < 0:
            raise MatchException(
                f"Index of header {ref['name']} is negative. Check the headers for your reference."
            )
        ls = []
        for line in result.lines:
            if len(line) > i and line[i] is not None:
                ls.append(f"{line[i]}".strip())
        return ls
