from typing import Any, List, Dict
from ..util.lark_print_parser import LarkPrintParser, LarkPrintTransformer


class PrintParserException(Exception):
    pass


class PrintParser:
    def __init__(self, csvpath=None):
        self.parser = None
        self.csvpath = csvpath

    def transform(self, printstr) -> str:
        self.parser = LarkPrintParser(csvpath=self.csvpath)

        tree = self.parser.parse(printstr)
        if self.csvpath:
            self.csvpath.logger.debug(tree.pretty())

        transformer = LarkPrintTransformer(self.csvpath)
        ts = transformer.transform(tree)

        return self._to_string(ts)

    def _to_string(self, ts) -> str:
        res = ""
        for item in ts:
            if isinstance(item, dict):
                item = self._handle_replacement(item)
            res = f"{res}{item}"
        return res

    def _handle_replacement(self, ref) -> str:
        if self._is_local(ref["root"]):
            return self._handle_local(ref)
        else:
            return self._handle_reference(ref)

    def _is_local(self, name) -> bool:
        name = name.strip()
        return name == "$."

    def _handle_local(self, ref) -> str:
        atype = ref["data_type"]
        data = None
        if atype == "variables":
            data = self.csvpath.variables
        elif atype == "headers":
            data = self.csvpath.headers
        elif atype == "metadata":
            data = self.csvpath.metadata
        elif atype == "csvpath":
            data = {}
            self._get_runtime_data_from_local(self.csvpath, data, local=True)
        ref["data"] = data
        self.csvpath.logger.debug(f"PrintParser._handle_local: local vars are: {data}")
        return self._transform_reference(ref)

    def _handle_reference(self, ref) -> str:
        name = ref["root"]
        name = name[1:]
        name = name.rstrip(".")
        if name == "":  # pragma: no cover
            self.csvpath.logger.error("Name cannot be empty")
            raise Exception("Name cannot be ''")
        results = self._get_results(ref, name)
        ref["named_paths"] = name
        if results is None:
            self.csvpath.logger.error(f"No results available for name '{name}'")
            return f"{ref}"
        ref["results"] = results
        atype = ref["data_type"]
        data = None
        if atype == "variables":
            data = self._get_variables(ref, results)
        elif atype == "headers":
            data = self._get_headers(ref, results)
        elif atype == "metadata":
            data = self._get_metadata(ref, results)
        elif atype == "csvpath":
            data = self._get_runtime_data_from_results(ref, results)
        ref["data"] = data
        return self._transform_reference(ref)

    def _transform_reference(self, ref) -> str:
        name = ref["name"][0]
        tracking = None
        if len(ref["name"]) > 1 and ref["name"][1] and ref["name"][1].strip() != "":
            tracking = ref["name"][1]
        data = ref["data"]
        self.csvpath.logger.debug(
            f"PrintParser._transform_reference: name: {name}; vars are: {data}"
        )
        if isinstance(data, dict):
            return self._ref_from_dict(ref, data, name, tracking)
        elif isinstance(data, list):
            return self._ref_from_list(ref, data, name, tracking)

    def _ref_from_list(self, ref, data, name, tracking):
        # find index of header
        if "results" in ref:
            c = ref["results"].csvpath
        else:
            c = self.csvpath
        i = c.header_index(name)
        #
        # i was -1 on a miss which wrapped. a miss is now None,
        # but checking for -1 doesn't hurt.
        #
        if i is None or i == -1:
            if f"{name}".isdigit():
                i = int(name)
            pass
        # if we're working on a reference to another csvpath than we are in
        # and if csvpaths and lines were collected, we could pull them from
        # the results. but for now we'll just use the matcher's last/current
        # line. if/when we want to allow indexing into the result lines this
        # will change.
        datum = name
        if c.matcher:
            try:
                datum = c.matcher.line[i]
            except Exception:
                self.csvpath.logger.warning(f"No matcher.line[{i}] available")

        if tracking is not None and tracking != "":
            #
            # note that today in Reference we do use tracking values on headers
            # to narrow results. if a tracking value matches an "id" or "name"
            # value in the metadata we pick that result set; otherwise the [0]
            # results. this may or may not become the main/standard way to select
            # specific csvpath results.
            #
            self.csvpath.logger.warning(  # pragma: no cover
                f"Found tracking {tracking} in reference {ref}. We don't use tracking codes on headers"
            )
        return datum

    def _ref_from_dict(self, ref, data, name, tracking):
        if name not in data:
            self.csvpath.logger.warning(f"No key '{name}' in data of ref {ref}")
            return name

        datum = data[name]
        iota = None
        if tracking is not None:
            if isinstance(datum, dict) and tracking in datum:
                iota = datum[tracking]
            elif isinstance(datum, list):
                if tracking == "length":
                    iota = len(datum)
                else:
                    try:
                        i = int(tracking)
                        iota = datum[i]
                    except Exception:  # pragma: no cover
                        self.csvpath.logger.warning(
                            f"Cannot index into list {datum} with {tracking} on reference {ref}"
                        )
                        iota = ""
            else:
                iota = ""  # pragma: no cover
        if iota is not None:
            return iota
        else:
            return datum

    def _get_results(self, ref, name):
        if not self.csvpath.csvpaths:
            return None  # pragma: no cover
        if not self.csvpath.csvpaths.results_manager:
            return None  # pragma: no cover
        return self.csvpath.csvpaths.results_manager.get_named_results(name)

    def _get_variables(self, ref, results):
        data = {}
        for i, result in enumerate(results):
            csvpath = result.csvpath
            v = csvpath.variables
            self.csvpath.logger.debug(f"PrintParser._get_variables: v: {v}")
            data = {**data, **v}
        return data

    def _get_headers(self, ref, results):
        data = {}
        for result in results:
            csvpath = result.csvpath
            identity = csvpath.identity
            data[identity] = {}
            hs = csvpath.headers
            for i, h in enumerate(hs):
                data[identity][h] = i
        return data

    def _get_metadata(self, ref, results):
        #
        # combine metadata for the run with metadata
        # about the individual csvpaths. last adder
        # wins.
        #
        data = self.csvpath.csvpaths.results_manager.get_metadata(ref["named_paths"])
        for result in results:
            csvpath = result.csvpath
            data = {**data, **csvpath.metadata}
        return data

    def _get_runtime_data_from_results(self, ref, results) -> None:
        data = {}
        for result in results:
            csvpath = result.csvpath
            self._get_runtime_data_from_local(csvpath, data)
        return data

    def _get_runtime_data_from_local(
        self, csvpath, runtime: Dict[str, Any], local=False
    ) -> None:
        identity = csvpath.identity
        #
        # Common to all csvpaths in results
        #
        if "delimiter" in runtime:
            if runtime["delimiter"] != csvpath.delimiter:
                raise PrintParserException(
                    f"Unalike delimiter: {identity}: {csvpath.delimiter}"
                )
        else:
            runtime["delimiter"] = csvpath.delimiter
        if "quotechar" in runtime:
            if runtime["quotechar"] != csvpath.quotechar:
                raise PrintParserException(
                    f"Unalike quotechar: {identity}: {csvpath.quotechar}"
                )
        else:
            runtime["quotechar"] = csvpath.quotechar
        runtime["file_name"] = csvpath.scanner.filename
        self._set(runtime, identity, "lines_time", csvpath.rows_time, local, True)
        self._set(
            runtime,
            identity,
            "total_lines",
            csvpath.line_monitor.data_end_line_count,
            True,
            True,
        )
        #
        # end of common-to-all
        #
        self._set(
            runtime,
            identity,
            "count_lines",
            csvpath.line_monitor.physical_line_count,
            local,
            False,
        )
        self._set(
            runtime,
            identity,
            "line_number",
            csvpath.line_monitor.physical_line_number,
            local,
            False,
        )
        self._set(runtime, identity, "identity", identity, local, False)
        self._set(runtime, identity, "count_matches", csvpath.match_count, local, False)
        self._set(runtime, identity, "count_scans", csvpath.scan_count, local, False)
        self._set(runtime, identity, "scan_part", csvpath.scan, local, False)
        self._set(runtime, identity, "match_part", csvpath.match, local, False)
        self._set(
            runtime, identity, "last_line_time", csvpath.last_row_time, local, False
        )
        #
        # headers can change. we lose the changes but can at least capture the potentially
        # different end states
        #
        self._set(runtime, identity, "headers", csvpath.headers, local, False)
        self._set(runtime, identity, "valid", csvpath.is_valid, local, False)
        self._set(runtime, identity, "stopped", csvpath.stopped, local, False)

    def _set(
        self, runtime, identity: str, name: str, value, local: bool, addative: False
    ) -> None:
        if local:
            runtime[name] = value
        else:
            if addative:
                if name in runtime:
                    runtime[name] += value
                else:
                    runtime[name] = value
            else:
                if name not in runtime:
                    runtime[name] = {}
                runtime[name][identity] = value
