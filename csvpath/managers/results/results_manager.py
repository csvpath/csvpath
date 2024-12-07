# pylint: disable=C0114
import os
from pathlib import Path
import datetime
from typing import Dict, List, Any
from csvpath.util.line_spooler import LineSpooler
from csvpath.util.exceptions import InputException, CsvPathsException
from csvpath.util.reference_parser import ReferenceParser
from ..run.run_metadata import RunMetadata
from ..run.run_registrar import RunRegistrar
from .results_metadata import ResultsMetadata
from .result_metadata import ResultMetadata
from .results_registrar import ResultsRegistrar
from .result_registrar import ResultRegistrar
from .result_serializer import ResultSerializer
from .result import Result


class ResultsManager:  # pylint: disable=C0115
    def __init__(self, *, csvpaths=None):
        self.named_results = {}
        self._csvpaths = None
        # use property
        self.csvpaths = csvpaths

    @property
    def csvpaths(self):
        return self._csvpaths

    @csvpaths.setter
    def csvpaths(self, cs) -> None:  # noqa: F821
        self._csvpaths = cs

    def complete_run(self, *, run_dir, pathsname, results) -> None:
        rr = ResultsRegistrar(
            csvpaths=self.csvpaths,
            run_dir=run_dir,
            pathsname=pathsname,
            results=results,
        )
        m = rr.manifest
        mdata = ResultsMetadata(self.csvpaths.config)
        if "time" not in m or m["time"] is None:
            mdata.set_time()
        else:
            mdata.time_string = m["time"]
        mdata.uuid_string = m["uuid"]
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.named_file_fingerprint = m["named_file_fingerprint"]
        mdata.named_file_fingerprint_on_file = m["named_file_fingerprint_on_file"]
        mdata.named_file_name = m["named_file_name"]
        mdata.named_file_path = m["named_file_path"]
        mdata.run_home = run_dir
        mdata.named_paths_name = pathsname
        mdata.named_results_name = pathsname
        rr.register_complete(mdata)

    def start_run(self, *, run_dir, pathsname, filename) -> None:
        rr = ResultsRegistrar(
            csvpaths=self.csvpaths,
            run_dir=run_dir,
            pathsname=pathsname,
        )
        mdata = ResultsMetadata(self.csvpaths.config)
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.named_file_name = filename
        # self.csvpaths.file_manager.get_named_file(filename)
        mdata.run_home = run_dir
        mdata.named_paths_name = pathsname
        mdata.named_results_name = pathsname
        rr.register_start(mdata)

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """gets the run metadata. will include the metadata complete from
        the first results. however, the metadata for individual results must
        come direct from them in order to not overwrite"""
        results = self.get_named_results(name)
        meta = {}
        if results and len(results) > 0:
            rs = results[0]
            path = rs.csvpath
            meta["paths_name"] = rs.paths_name
            meta["file_name"] = rs.file_name
            meta["data_lines"] = path.line_monitor.data_end_line_count
            paths = len(self.csvpaths.paths_manager.get_named_paths(name))
            meta["csvpaths_applied"] = paths
            meta["csvpaths_completed"] = paths == len(results)
            meta["valid"] = self.is_valid(name)
            meta = {**meta, **rs.csvpath.metadata}
        return meta

    def get_specific_named_result(self, name: str, name_or_id: str) -> Result:
        results = self.get_named_results(name)
        if results and len(results) > 0:
            for r in results:
                if name_or_id == r.csvpath.identity:
                    return r
        return None  # pragma: no cover

    def get_specific_named_result_manifest(
        self, name: str, name_or_id: str
    ) -> dict[str, str | bool]:
        r = self.get_specific_named_result(name, name_or_id)
        if r is None:
            return None
        rs = ResultSerializer(self._csvpaths.config.archive_path)
        rr = ResultRegistrar(csvpaths=self.csvpaths, result=r, result_serializer=rs)
        return rr.manifest

    def get_last_named_result(self, *, name: str, before: str = None) -> Result:
        results = self.get_named_results(name)
        if results and len(results) > 0:
            return results[len(results) - 1]
        return None

    def is_valid(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if not r.is_valid:
                return False
        return True

    def get_variables(self, name: str) -> bool:
        results = self.get_named_results(name)
        vs = {}
        for r in results:
            vs = {**r.csvpath.variables, **vs}
        return vs

    def has_lines(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if r.lines and len(r.lines) > 0:
                return True
        return False

    def get_number_of_results(self, name: str) -> int:
        nr = self.get_named_results(name)
        if nr is None:
            return 0
        return len(nr)

    def has_errors(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if r.has_errors():
                return True
        return False

    def get_number_of_errors(self, name: str) -> bool:
        results = self.get_named_results(name)
        errors = 0
        for r in results:
            errors += r.errors_count()
        return errors

    def add_named_result(self, result: Result) -> None:
        if result.file_name is None:
            raise InputException("Results must have a named-file name")
        if result.paths_name is None:
            raise InputException("Results must have a named-paths name")
        name = result.paths_name
        if name not in self.named_results:
            self.named_results[name] = [result]
        else:
            self.named_results[name].append(result)
        self._variables = None
        #
        # this is the beginning of an identity run within a named-paths run.
        # run metadata goes to the central record of runs kicking off within
        # the archive. the run's own more complete record is below as a
        # separate event. this could change, but atm seems reasonable.
        #

        mdata = RunMetadata(self.csvpaths.config)
        mdata.uuid = result.uuid
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.time_start = result.run_time
        mdata.run_home = result.run_dir
        mdata.identity = result.identity_or_index
        mdata.named_paths_name = result.paths_name
        mdata.named_file_name = result.file_name
        rr = RunRegistrar(self.csvpaths)
        rr.register_start(mdata)

        #
        # we prep the results event
        #
        # we use the same UUID for both metadata updates because the
        # UUID represents the run, not the metadata object
        #

        mdata = ResultMetadata(self.csvpaths.config)
        mdata.uuid = result.uuid
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.time_started = result.run_time
        mdata.named_results_name = result.paths_name
        mdata.run = result.run_dir[result.run_dir.rfind(os.sep) + 1 :]
        mdata.run_home = result.run_dir
        mdata.instance_home = result.instance_dir
        mdata.instance_identity = result.identity_or_index
        mdata.input_data_file = result.file_name
        rs = ResultSerializer(self._csvpaths.config.archive_path)
        rr = ResultRegistrar(
            csvpaths=self.csvpaths, result=result, result_serializer=rs
        )
        rr.register_start(mdata)

    def set_named_results(self, results: Dict[str, List[Result]]) -> None:
        self.named_results = {}
        for value in results.values():
            self.add_named_results(value)

    def add_named_results(self, results: List[Result]) -> None:
        for r in results:
            self.add_named_result(r)

    def list_named_results(self) -> list[str]:
        path = self._csvpaths.config.archive_path
        names = os.listdir(path)
        names = [n for n in names if not n.startswith(".")]
        names.sort()
        return names

    def do_transfers_if(self, result) -> None:
        transfers = result.csvpath.transfers
        if transfers is None:
            return
        tpaths = self.transfer_paths(result)
        self._do_transfers(tpaths)

    def transfer_paths(self, result) -> list[tuple[str, str, str, str]]:
        #
        # 1: filename, no extension needed: data | unmatched
        # 2: variable name containing the path to write to
        # 3: path of source file
        # 3: path to write to
        #
        transfers = result.csvpath.transfers
        tpaths = []
        for t in transfers:
            filefrom = "data.csv" if t[0].startswith("data") else "unmatched.csv"
            varname = t[1]
            pathfrom = self._path_to_result(result, filefrom)
            pathto = self._path_to_transfer_to(result, varname)
            tpaths.append((filefrom, varname, pathfrom, pathto))
        return tpaths

    def _do_transfers(self, tpaths) -> None:
        for t in tpaths:
            pathfrom = t[2]
            pathto = t[3]
            with open(pathfrom, "r", encoding="utf-8") as pf:
                with open(pathto, "w", encoding="utf-8") as pt:
                    pt.write(pf.read())

    def _path_to_transfer_to(self, result, t) -> str:
        p = result.csvpath.config.transfer_root
        if t not in result.csvpath.variables:
            raise InputException(f"Variable {t} not found in variables")
        f = result.csvpath.variables[t]
        if f.find("..") != -1:
            raise InputException("Transfer path cannot include '..': {f}")
        rp = os.path.join(p, f)
        rd = rp[0 : rp.rfind(os.sep)]
        if not os.path.exists(rd):
            Path(rd).mkdir(parents=True, exist_ok=True)
        return rp

    def _path_to_result(self, result, t) -> str:
        d = result.instance_dir
        o = os.path.join(d, t)
        r = o[0 : o.rfind(os.sep)]
        if not os.path.exists(r):
            os.mkdirs(r)
            Path(r).mkdir(parents=True, exist_ok=True)
        return o

    def save(self, result: Result) -> None:
        if self._csvpaths is None:
            raise CsvPathsException("Cannot save because there is no CsvPaths instance")
        if result.lines and isinstance(result.lines, LineSpooler):
            # we are done spooling. need to close whatever may be open.
            result.lines.close()
            # cannot make lines None w/o recreating lines. now we're setting
            # closed to true to indicate that we've written.
            # we don't need the serializer trying to save spooled lines
            # result.lines = None
        #
        # if we are doing a transfer(s) do it here so we can put metadata in about
        # the copy before the metadata is serialized into the results.
        #
        self.do_transfers_if(result)
        rs = ResultSerializer(self._csvpaths.config.archive_path)
        rs.save_result(result)
        ResultRegistrar(
            csvpaths=self.csvpaths, result=result, result_serializer=rs
        ).register_complete()

    # in this form: $group.results.2024-01-01_10-15-20.mypath
    def data_file_for_reference(self, refstr) -> str:
        ref = ReferenceParser(refstr)
        if ref.datatype != ReferenceParser.RESULTS:
            raise InputException(
                f"Reference datatype must be {ReferenceParser.RESULTS}"
            )
        namedpaths = ref.root_major
        instance = ref.name_one
        path = ref.name_three
        base = self._csvpaths.config.archive_path
        filename = os.path.join(base, namedpaths)
        if not os.path.exists(filename):
            raise InputException(
                "Reference does not point to a previously run named-paths group"
            )
        #
        # instance can have var-subs like:
        #   2024-01-01_10-15-:last
        #   2024-01-01_10-:first
        #   2024-01-01_10-:0
        #
        instance = self._find_instance(filename, instance)
        filename = os.path.join(filename, instance)
        if not os.path.exists(filename):
            raise InputException(
                f"Reference {refstr} does not point to a valid named-paths run file at {filename}"
            )
        filename = os.path.join(filename, path)
        if not os.path.exists(filename):
            raise InputException(
                f"Reference to {filename} does not point to a csvpath in a named-paths group run"
            )
        filename = os.path.join(filename, "data.csv")
        if not os.path.exists(filename):
            raise InputException(
                "Reference does not point to a data file resulting from a named-paths group run"
            )
        return filename

    def _find_instance(self, filename, instance) -> str:
        """remember that you cannot replay a replay using :last. the reason is that both
        runs will be looking for the same assets but the last replay run will not have
        the asset needed. in principle, we could fix this, but in practice, any magic
        we do to make it always work is going to make the lineage more mysterious.
        """
        c = instance.find(":")
        if c == -1:
            filename = os.path.join(filename, instance)
            return filename
        if not os.path.exists(filename):
            raise InputException(f"The base dir {filename} must exist")
        var = instance[c:]
        instance = instance[0:c]
        ret = None
        if var == ":last":
            ret = self._find_last(filename, instance)
        elif var == ":first":
            ret = self._find_first(filename, instance)
        else:
            raise InputException(f"Unknown reference var-sub token {var}")
        return ret

    def _find_last(self, filename, instance) -> str:
        last = True
        return self._find(filename, instance, last)

    def _find_first(self, filename, instance) -> str:
        first = False
        return self._find(filename, instance, first)

    def _find(self, filename, instance, last: bool = True) -> str:
        names = os.listdir(filename)
        return self._find_in_dir_names(instance, names, last)

    def _find_in_dir_names(self, instance: str, names, last: bool = True) -> str:
        ms = "%Y-%m-%d_%H-%M-%S.%f"
        s = "%Y-%m-%d_%H-%M-%S"
        names = [n for n in names if n.startswith(instance)]
        if len(names) == 0:
            return None
        names = sorted(
            names,
            key=lambda x: datetime.datetime.strptime(x, ms if x.find(".") > -1 else s),
        )
        if last is True:
            i = len(names)
            #
            # we drop 1 because -1 for the 0-base. note that we may find a replay
            # run that doesn't have the asset we're looking for. that's not great
            # but it is fine -- the rule is, no replays of replays using :last.
            # it is on the user to set up their replay approprately.
            #
            i -= 1
            if i < 0:
                self.csvpaths.logger.error(
                    f"Previous run is at count {i} but there is no such run. Returning None."
                )
                self.csvpaths.logger.info(
                    "Found previous runs: %s matching instance: %s", names, instance
                )
                return None
            ret = names[i]
        else:
            ret = names[0]
        return ret

    def get_run_time_str(self, name, run_time) -> str:
        rs = ResultSerializer(self._csvpaths.config.archive_path)
        t = rs.get_run_dir(paths_name=name, run_time=run_time)
        return t

    def remove_named_results(self, name: str) -> None:
        #
        # does not get rid of results on disk
        #
        if name in self.named_results:
            del self.named_results[name]
            self._variables = None
        else:
            self.csvpaths.logger.warning(f"Results '{name}' not found")
            #
            # we treat this as a recoverable error because typically the user
            # has complete control of the csvpaths environment, making the
            # problem config that should be addressed.
            #
            # if reached by a reference this error should be trapped at an
            # expression and handled according to the error policy.
            #
            raise InputException(f"Results '{name}' not found")

    def clean_named_results(self, name: str) -> None:
        if name in self.named_results:
            self.remove_named_results(name)
            #
            # clean from filesystem too?
            #

    def get_named_results(self, name) -> List[List[Any]]:
        if name in self.named_results:
            return self.named_results[name]
        #
        # we treat this as a recoverable error because typically the user
        # has complete control of the csvpaths environment, making the
        # problem config that should be addressed.
        #
        # if reached by a reference this error should be trapped at an
        # expression and handled according to the error policy.
        #
        raise InputException(
            f"Results '{name}' not found. \nNamed-results are: {self.named_results}"
        )
