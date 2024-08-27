from typing import Any, List, Dict
from ..util.lark_print_parser import LarkPrintParser, LarkPrintTransformer
from csvpath.util.exceptions import ConfigurationException


class PrintParser:
    def __init__(self, csvpath):
        self.parser = None
        self.csvpath = csvpath

    def transform(self, printstr) -> str:
        self.parser = LarkPrintParser()
        tree = self.parser.parse(printstr)
        transformer = LarkPrintTransformer(self)
        ts = transformer.transform(tree)
        self.csvpath.logger.debug(
            f"PrintParser.transform: printstr: {printstr} ==> transformed tree: {ts}"
        )
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
            self._get_data(self.csvpath, data)
        ref["data"] = data
        return self._transform_reference(ref)

    def _handle_reference(self, ref) -> str:
        name = ref["root"]
        name = name[1:]
        name = name.rstrip(".")
        if name == "":
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
            data = self._get_runtime_data(ref, results)
        ref["data"] = data
        return self._transform_reference(ref)

    def _transform_reference(self, ref) -> str:
        name = ref["name"][0]
        tracking = None
        if len(ref["name"]) > 1:
            tracking = ref["name"][1]
        data = ref["data"]
        if isinstance(data, dict):
            return self._ref_from_dict(ref, data, name, tracking)
        elif isinstance(data, list):
            return self._ref_from_list(ref, data, name, tracking)

    def _ref_from_list(self, ref, data, name, tracking):
        # find index of header
        c = ref["results"].csvpath if "results" in ref else self.csvpath
        i = c.header_index(name)
        # if csvpaths and lines were collected, we could pull them from
        # the results. for now we'll just use the matcher's last line.
        # if/when we want to allow indexing into the result lines this will
        # change.
        if c.matcher:
            try:
                datum = c.matcher.line[i]
            except Exception:
                self.csvpath.logger.warning(f"No matcher.line[{i}] available")
        else:
            datum = name
        if tracking is not None and tracking != "":
            self.csvpath.logger.warning(
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
                    except Exception:
                        self.csvpath.logger.warning(
                            f"Cannot index into list {datum} with {tracking} on reference {ref}"
                        )
                        iota = ""
            else:
                iota = ""
        if iota is not None:
            return iota
        else:
            return datum

    def _get_results(self, ref, name):
        if not self.csvpath.csvpaths:
            return None
        if not self.csvpath.csvpaths.path_results_manager:
            return None
        return self.csvpath.csvpaths.path_results_manager.get_named_results(name)

    def _get_variables(self, ref, results):
        data = {}
        for i, result in enumerate(results):
            csvpath = result.csvpath
            v = csvpath.variables
            data = {**data, **v}
        return data

    def _get_headers(self, ref, results):
        data = {}
        for result in results:
            csvpath = result.csvpath
            hs = csvpath.headers
            for i, h in enumerate(hs):
                data = {h, i}
        return data

    def _get_metadata(self, ref, results):
        #
        # combine metadata for the run with metadata
        # about the individual csvpaths. last adder
        # wins.
        #
        data = self.csvpath.csvpaths.path_results_manager.get_metadata(
            ref["named_paths"]
        )
        for result in results:
            csvpath = result.csvpath
            data = {**data, **csvpath.metadata}
        return data

    def _get_runtime_data(self, ref, results) -> None:
        data = {}
        for result in results:
            csvpath = result.csvpath
            self._get_data(csvpath, data)
        return data

    def _get_data(self, csvpath, runtime: Dict[str, Any]) -> None:
        runtime["name"] = csvpath._run_name

        if "delimiter" in runtime:
            if runtime["delimiter"] != csvpath.delimiter:
                raise ConfigurationException(
                    "Unalike delimiter for same run: {runtime['name']}"
                )
        else:
            runtime["delimiter"] = csvpath.delimiter

        if "quotechar" in runtime:
            if runtime["quotechar"] != csvpath.delimiter:
                raise ConfigurationException(
                    "Unalike quotechar for same run: {runtime['name']}"
                )
        else:
            runtime["quotechar"] = csvpath.quotechar

        if "count_matches" in runtime:
            runtime["count_matches"] += csvpath.match_count
        else:
            runtime["count_matches"] = csvpath.match_count

        if "count_lines" in runtime:
            runtime["count_lines"] += csvpath.line_number
        else:
            runtime["count_lines"] = csvpath.line_number

        if "count_scans" in runtime:
            runtime["count_scans"] += csvpath.scan_count
        else:
            runtime["count_scans"] = csvpath.scan_count

        runtime["scan_part"] = csvpath.scan
        runtime["match_part"] = csvpath.match
        runtime["last_row_time"] = csvpath.last_row_time

        if "rows_time" in runtime:
            runtime["rows_time"] += csvpath.rows_time
        else:
            runtime["rows_time"] = csvpath.rows_time

        runtime["rows_time"] = csvpath.rows_time
        runtime["total_lines"] = csvpath.total_lines
        #
        # if the author named the csvpath use that to identify if it is valid.
        #
        id = "csvpath" if "name" not in csvpath.metadata else csvpath.metadata["name"]
        if id.strip() == "":
            id = "csvpath"
        if "failed" not in runtime:
            runtime["failed"] = {}
        runtime["failed"][id] = not csvpath.is_valid
        runtime["stopped"] = csvpath.stopped
