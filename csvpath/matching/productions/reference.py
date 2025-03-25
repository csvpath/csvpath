# pylint: disable=C0114
from typing import Any, Dict, List
from csvpath.matching.productions.matchable import Matchable
from ..util.exceptions import MatchException, DataException


class Reference(Matchable):
    """reference is to specific variable values or an existence test against a header's values"""

    #
    # the Reference class only deals with runtime metadata (vars, headers, csvpath)
    # and named-paths ("csvpaths"). atm, METADATA is aspirational, if even needed.
    #
    VARIABLES = "variables"
    HEADERS = "headers"
    CSVPATHS = "csvpaths"
    CSVPATH = "csvpath"
    METADATA = "metadata"

    def check_valid(self) -> None:  # pylint: disable=W0246
        # re: W0246: Matchable handles this class's children
        super().check_valid()

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        if name is None:
            msg = "Name cannot be None"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        if name.strip() == "":
            msg = "Name cannot be the empty string"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        #
        # references are in the form:
        #    $path.(csvpath|metadata|variable|header).name[.tracking_name/index]
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
            ret = self._noop_match()  # pragma: no cover
            self.matching().result(ret).because("skip")
            return ret
        if self.match is None:
            if self.value is None:
                self.to_value(skip=skip)
            self.match = self.value is not None
            self.matching().result(self.match)
        return self.match  # pragma: no cover

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:
            ret = self._noop_value()  # pragma: no cover
            self.valuing().result(ret).because("skip")
            return ret
        if self.value is None:
            self.matcher.csvpath.logger.info(
                "Beginning a lookup on %s", self
            )  # pragma: no cover
            ref = self._get_reference()
            if ref["data_type"] == Reference.HEADERS:
                if self._cache_vars is not None:
                    self.value = self._cache_headers
                else:
                    self.value = self._header_value()
                    self._cache_headers = self.value
            elif ref["data_type"] == Reference.VARIABLES:
                if self._cache_vars is not None:
                    self.value = self._cache_vars
                else:
                    self.value = self._variable_value()
                    self._cache_vars = self.value
            elif ref["data_type"] == Reference.CSVPATHS:
                self.value = f"{ref['paths_name']}#{ref['name']}"
            else:
                msg = "Incorrect reference data type: {ref['data_type']}"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        self.valuing().result(self.value)
        return self.value

    def data_type(self):
        ref = self._get_reference()
        return ref["data_type"]

    def is_header(self):
        return self.data_type() == "headers"

    def is_variable(self):
        return self.data_type() != "headers"

    def data_name(self):
        """this is the name of the datum being referred to. however, it
        is not the tracking value. that is on the "tracking" key in the ref."""
        ref = self._get_reference()
        return ref["name"]

    def tracking_name(self):
        """this is the name of the tracking value."""
        ref = self._get_reference()
        return ref["tracking"]

    @property
    def reference_names(self) -> Dict[str, str]:
        self._get_reference()

    def _get_reference(self) -> Dict[str, str]:
        if self.ref is None:
            self.ref = self._get_reference_for_parts(self.name_parts)
        return self.ref

    def _get_reference_for_parts(self, name_parts: List[str]) -> Dict[str, str]:
        ref = {}
        if name_parts[1] in [
            Reference.VARIABLES,
            Reference.HEADERS,
            Reference.CSVPATHS,
        ]:
            ref["paths_name"] = name_parts[0]
            ref["data_type"] = name_parts[1]
            ref["name"] = name_parts[2]
            ref["tracking"] = name_parts[3] if len(name_parts) == 4 else None
        # the next few lines are harmless but dead. they likely will come back. atm
        # they trigger coverage
        else:
            ref["paths_name"] = name_parts[0]
            ref["data_type"] = name_parts[1]
            ref["name"] = name_parts[2]
            ref["tracking"] = name_parts[3] if len(name_parts) == 4 else None
        #
        # assuming we're cutting this off here because we don't yet support
        # metadata and csvpaths in plain references yet. we do support
        # them in print references.
        #
        if ref["data_type"] not in [
            Reference.VARIABLES,
            Reference.HEADERS,
            Reference.CSVPATHS,
        ]:
            msg = f"""References must be to variables or headers, not {ref["data_type"]}"""
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        return ref

    def _variable_value(self) -> Any:
        ref = self._get_reference()
        cs = self.matcher.csvpath.csvpaths  # pragma: no cover
        if cs is None:
            msg = "References cannot be used without a CsvPaths instance"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
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
            msg = f"Results exist but the {ref['name']} variable is unknown: {self.my_chain}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise DataException(msg)
        return ret

    def _header_value(self) -> Any:
        ref = self._get_reference()
        r = self.get_results()
        return self._get_value_from_results(ref, r)

    def get_results(self) -> Any:
        ref = self._get_reference()
        name = ref["paths_name"]
        rm = self.matcher.csvpath.csvpaths.results_manager
        if rm.has_lines(name):
            #
            # we pull data. if we have a tracking value we can pull a specific csvpath's result
            #
            if rm.get_number_of_results(name) == 1:
                rs = rm.get_named_results(name)
                return rs[0]
            if ref["tracking"]:
                #
                # find the specific path if we have a tracking value.
                # tested in test_reference_specific_header_lookup. manager has 100% coverage.
                #
                r = rm.get_specific_named_result(
                    name, ref["tracking"]
                )  # pragma: no cover
                if r is None:
                    #
                    # dispatch error event
                    # -- then --
                    # self.matcher.csvpath.ecomms.do_i_raise()
                    #
                    raise MatchException(
                        f"No results in {name} for metadata {ref['tracking']} in {self}"
                    )
                return r
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
        raise MatchException("Results may exist but no data was captured")

    def _get_value_from_results(self, ref, result):
        csvpath = result.csvpath
        i = csvpath.header_index(ref["name"])
        if i < 0:
            raise MatchException(
                f"Index of header {ref['name']} is negative. Check the headers for your reference."
            )
        ls = []
        for line in result.lines.next():
            if len(line) > i and line[i] is not None:
                ls.append(f"{line[i]}".strip())
        return ls
