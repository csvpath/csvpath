# pylint: disable=C0114
import os
import json
import re
from uuid import UUID
from pathlib import Path
import datetime
import dateutil.parser
from typing import Dict, List, Any
from csvpath.util.line_spooler import LineSpooler
from csvpath.util.exceptions import InputException, CsvPathsException
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.results_reference_finder_2 import (
    ResultsReferenceFinder2 as ResultsReferenceFinder,
)
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.scanning.scanner import Scanner
from ..run.run_metadata import RunMetadata
from ..run.run_registrar import RunRegistrar
from .results_metadata import ResultsMetadata
from .result_metadata import ResultMetadata
from .results_registrar import ResultsRegistrar
from .result_registrar import ResultRegistrar
from .result_serializer import ResultSerializer
from .result import Result
from .result_file_reader import ResultFileReader
from csvpath.util.template_util import TemplateUtility as temu


class ResultsManager:  # pylint: disable=C0115
    def __init__(self, *, csvpaths=None):
        """@private"""
        self.named_results = {}
        """@private"""
        self._csvpaths = None
        # use property
        self.csvpaths = csvpaths
        """@private"""

    @property
    def csvpaths(self):
        """@private"""
        return self._csvpaths

    @csvpaths.setter
    def csvpaths(self, cs) -> None:  # noqa: F821
        """@private"""
        self._csvpaths = cs

    def complete_run(self, *, run_dir, pathsname, results) -> None:
        """@private"""
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
        mdata.number_of_files_expected = -1
        mdata.number_of_files_generated = -1

        rr.register_complete(mdata)

    #
    # since the filename may be a reference that picks out multiple files
    # we pass the physical data file. if file_manager receives that it
    # will look in the named-file manifest for the registration that matches
    # and return that uuid.
    #
    def start_run(
        self, *, run_dir, pathsname, filename, file: str = None, run_uuid: UUID
    ) -> None:
        """@private"""
        rr = ResultsRegistrar(
            csvpaths=self.csvpaths,
            run_dir=run_dir,
            pathsname=pathsname,
        )
        #
        # collect the named-paths and named-file uuids. these may
        # need to come from a different source at some point but
        # pulling them from the managers insulates us a bit.
        #
        np_uuid = self.csvpaths.paths_manager.get_named_paths_uuid(pathsname)
        if np_uuid is None:
            raise ValueError("named_paths_uuid cannot be None")
        f_uuid = self.csvpaths.file_manager.get_named_file_uuid(
            name=filename, file=file
        )
        if f_uuid is None:
            raise ValueError("named_file_uuid cannot be None")
        #
        #
        #
        mdata = ResultsMetadata(self.csvpaths.config)
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.run_home = run_dir
        mdata.run_uuid = run_uuid
        mdata.named_file_name = filename
        mdata.named_file_uuid = f"{f_uuid}"
        mdata.named_paths_name = pathsname
        mdata.named_paths_uuid = f"{np_uuid}"
        mdata.named_results_name = pathsname
        rr.register_start(mdata)
        return mdata

    #
    # this new version gets all the metadata from first through last member of the
    # named-paths group. last key added wins. if you need to be sure one csvpath
    # doesn't stomp on the last iterate the result objects yourself.
    #
    def get_metadata(self, name: str) -> bool:
        results = self.get_named_results(name)
        vs = {}
        for r in results:
            vs = {**r.csvpath.metadata, **vs}
        return vs

    #
    # unlike get_variables and get_metadata, get_errors adds lists with no chance for loss.
    #
    def get_errors(self, name: str) -> bool:
        results = self.get_named_results(name)
        es = []
        for r in results:
            es += r.csvpath.errors
        return es

    def get_specific_named_result(self, name: str, name_or_id: str = None) -> Result:
        #
        # ideally we need to handle two things:
        #   1: name=mygroup, name_or_id=myinstance
        #   2: $mygroup.results.path-to-run_dir.myinstance#[variables|headers|csvpath|metadata|errors|printouts]
        #

        if name is None:
            raise ValueError("Name cannot be none")
        if name_or_id is None:
            if name.startswith("$"):
                ref = ReferenceParser(name, csvpaths=self.csvpaths)
                if ref.root_minor is not None:
                    name_or_id = ref.root_minor
                elif ref.name_three is not None:
                    name_or_id = ref.name_three
                else:
                    #
                    # assuming the instance name_or_id is in the ref's name_one,
                    # this could be reasonable. or it may be user-error. if the user
                    # really wanted a date or template path to run_dir, this would be
                    # off base. but if they are looking for just the most recent run's
                    # instance it would at least make sense, but, regardless, would
                    # still not be ok.
                    #
                    raise ValueError("You must identity which run")
        if name_or_id is None:
            raise ValueError("Instance name cannot be none")
        results = self.get_named_results(name)
        if results is not None and not isinstance(results, list):
            return results
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

    #
    # returns the last run of name's last csvpath instance result object.
    # seems like an odd use case to support with its own method. needed?
    #
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
        """@private"""
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
        """@private"""
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
        mdata.run_uuid = result.run_uuid
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.archive_path = self.csvpaths.config.archive_path
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
        mdata.run_uuid = result.run_uuid
        mdata.archive_name = self.csvpaths.config.archive_name
        mdata.time_started = result.run_time
        mdata.named_results_name = result.paths_name
        sep = Nos(result.run_dir).sep
        mdata.run = result.run_dir[result.run_dir.rfind(sep) + 1 :]
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
        """@private"""
        self.named_results = {}
        for value in results.values():
            self.add_named_results(value)

    def add_named_results(self, results: List[Result]) -> None:
        """@private"""
        for r in results:
            self.add_named_result(r)

    #
    # this name is somewhat confusing. we're listing the names of results, not the
    # runs of the names. that means we're returning the flat list of paths-names/
    # results-names directly below the archive root. if we were listing actual runs
    # the challenge would be greater because templates allow for different structures
    # below the flat named-results list, but that's not what we're doing.
    #
    def list_named_results(self) -> list[str]:
        path = self._csvpaths.config.archive_path
        if Nos(path).dir_exists():
            names = Nos(path).listdir()
            #
            # listing dir shouldn't return manifest.json or any file. can do better here.
            #
            names = [
                n for n in names if not n.startswith(".") and not n.endswith(".json")
            ]
            names.sort()
        else:
            self._csvpaths.logger.warning(
                "Archive %s does not exist. If no runs have been attempted yet this is fine.",
                path,
            )
            names = []
        return names

    def do_transfers_if(self, result) -> None:
        """@private"""
        transfers = result.csvpath.transfers
        if transfers is None:
            return
        tpaths = self.transfer_paths(result)
        self._do_transfers(tpaths)

    def transfer_paths(self, result) -> list[tuple[str, str, str, str]]:
        """@private"""
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
        """@private"""
        for t in tpaths:
            pathfrom = t[2]
            pathto = t[3]
            with DataFileReader(pathfrom) as pf:
                dfw = DataFileWriter(path=pathto, mode="w")
                dfw.write(pf.read())

    def _path_to_transfer_to(self, result, t) -> str:
        """@private"""
        p = result.csvpath.config.transfer_root
        if t not in result.csvpath.variables:
            raise InputException(f"Variable {t} not found in variables")
        f = result.csvpath.variables[t]
        if f.find("..") != -1:
            raise InputException("Transfer path cannot include '..': {f}")
        rp = os.path.join(p, f)
        sep = Nos(rp).sep
        rd = rp[0 : rp.rfind(sep)]
        if not Nos(rd).exists():
            Nos(rd).makedir()
        return rp

    def _path_to_result(self, result, t) -> str:
        """@private"""
        d = result.instance_dir
        o = os.path.join(d, t)
        sep = Nos(o).sep
        r = o[0 : o.rfind(sep)]
        if not Nos(r).exists():
            Nos(r).makedirs()
            Nos(r).makedir()
        return o

    def save(self, result: Result) -> None:
        """@private"""
        #
        # at this time we're not holding on to the result. we have a place for that,
        # but for now not holding forces the deserialization to work completely, so
        # it is worth more than the minor speed up of caching.
        #
        if self._csvpaths is None:
            raise CsvPathsException("Cannot save because there is no CsvPaths instance")
        if result.lines and isinstance(result.lines, LineSpooler):
            # we are done spooling. need to close whatever may be open.
            result.lines.close()
            # cannot make lines None w/o recreating lines. now we're setting
            # closed to true to indicate that we've written. we don't need the
            # serializer trying to save spooled lines result.lines = None
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

    def remove_named_results(self, name: str) -> None:
        """@private"""
        #
        # TODO: does not get rid of results on disk
        #
        if name in self.named_results:
            del self.named_results[name]
            self._variables = None
        else:
            self.csvpaths.logger.warning(f"Results '{name}' not found")

    #
    # @deprecated. use remove_named_results
    #
    def clean_named_results(self, name: str) -> None:
        """@private"""
        if name in self.named_results:
            self.remove_named_results(name)

    def all_run_dir_names(self, path, count) -> dict:
        mydirs = {}
        if count >= 0:
            nos = Nos(path)
            dirs = nos.listdir(dirs_only=True, recurse=True)
            for d in dirs:
                m = re.search(r"^.*\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(_\d)?", d)
                if m is not None:
                    d = m.group(0)
                    name = os.path.basename(d)
                    mydirs[name] = d
        else:
            mydirs[os.path.dirname(path)] = path
        return mydirs

    def _get_named_results_for_reference(self, name: str) -> List[List[Any]]:
        #
        # $mygroup.results.orders/acme/2025:first.myinstance
        #
        ref = ReferenceParser(name, csvpaths=self.csvpaths)
        if ref.datatype == ref.RESULTS:
            reff = ResultsReferenceFinder(self.csvpaths, reference=name)
            #
            # we don't need the finder to identify the instance. we'll do
            # ourselves. which is helpful if we're using name_four. the
            # suffix is a nagging worry.
            #
            results = reff.query()
            #
            # name = the named-paths / named-results name
            # run = the path to run_dir minus the archive/name root
            # path = the full path to the run_dir
            if len(results.files) == 0:
                msg = f"Results '{name}' does not exist"
                self.csvpaths.logger.error(msg)
                if self.csvpaths.ecoms.do_i_raise():
                    raise InputException(msg)
            path = results.files[0]
            run = path[len(self.csvpaths.config.archive_name) :]
            nos = Nos(path)
            run = run[run.find(nos.sep) + 1 :]
            #
            #
            #
            if ref.name_three is None:
                return self._get_named_results_for_run(
                    name=ref.root_major, run=run, path=path
                )
            if path.endswith(ref.name_three):
                path = os.path.dirname(path)
            return self.get_named_result_for_instance(
                name=ref.root_major, run_dir=path, run=run, instance=ref.name_three
            )
        elif ref.datatype == ref.CSVPATHS:
            #
            # if we're trying to get results using a named-paths reference
            # we must be reusing a named-paths reference that started the run
            # in that case, we're just looking for the named-paths name, not
            # anything more specific, so we'll try again passing only the
            # root, the named-paths name.
            #
            return self.get_named_results(ref.root_major)
        else:
            raise ValueError(f"Unexpected reference datatype in: {ref}")

    #
    # effectively, get last named results. use reference for anything more specific.
    #
    def get_named_results(self, name) -> List[List[Any]]:
        #
        # as it turns out, references are (finally!) the easiest, so let's do that
        # first.
        #
        if name is None:
            raise ValueError("Name cannot be None")
        if name.startswith("$"):
            return self._get_named_results_for_reference(name)
        #
        # CsvPaths instances should not be long lived. they are not servers or
        # agents. for each new run, unless there is a reason to not create a new
        # CsvPaths instance, we would create a new one.
        #
        if name in self.named_results:
            #
            # exp. removed 4 May.
            # was/is this ever a good idea?
            #
            # seems to be important for a handful of unit tests.
            #
            rs = self.named_results[name]
            return rs
        #
        # find and load the result, if exists. we find results home with the name. run_home is the
        # last run dir. the results we're looking for are the instance dirs in the run dir.
        # we'll need another method for getting a specific run, rather than the default, the last one.
        #
        # use r̶u̶n̶_̶h̶o̶m̶e̶_̶m̶a̶k̶e̶r̶.r̶u̶n̶s̶_̶h̶o̶m̶e̶_̶f̶r̶o̶m̶_̶t̶e̶m̶p̶l̶a̶t̶e̶ OR an index.json in the named-results root to
        # find the parent of the runs do the join below with that.
        #
        path = os.path.join(self.csvpaths.config.archive_path, name)
        self.csvpaths.logger.debug(
            "Attempting to load results for %s from %s", name, path
        )
        #
        # find the template. it comes from the named-paths so from the named-paths mgr
        #
        template = self._csvpaths.paths_manager.get_template_for_paths(name)
        if template is not None and not template == "":
            temu.valid(template)
        else:
            template = ""
        #
        # we should check here to make sure the template ends with :run_dir. that is a
        # requirement as of June 2025. it is basically the same as :filename in named-files
        # templates. originally there could be additional directories below :run_dir, but
        # that makes trouble with the new grammar-based refs and in any case was always
        # pretty illogical.
        #
        #
        # "top" of template. inserted dirs
        #
        run = None
        if template is not None and not template.strip() == "":
            #
            # TODO: there were concerns here pre-complete re the template changes.
            #
            t = template[0 : template.find(":run_dir")]
            t2 = template[template.find(":run_dir") + 8 :]
            c = t.count("/")  # or \\?
            c = c if c > -1 else t.count("\\")
            #
            # problem is here: vvvvv in all_run_dir_names()
            #
            runs = self.all_run_dir_names(path, c)
            names = list(runs.keys())
            #
            # there should be only run_dir names in names here. we sort based on
            # them. but we need to get the original template-based name. i.e. we
            # want 'aprx/2025-01-01...' not just '2025-01-01...'. that means we
            # need the full template name and then sort on the os.path.dirname(path).
            #
            # atm, all_run_dir_names() is not giving the full template name. and
            # it is also giving us names of instances within run_dirs. why? we
            # definitely don't want those.
            #
            names.sort()
            run = ""
            if len(names) > 0:
                run = names[len(names) - 1]
            rpath = runs[run]
            rpath = rpath[len(path) + 1 :]
            if t2 and len(t2) > 0:
                rpath = f"{rpath}{t2}"
            run = rpath
        else:
            #
            # original pre-template logic
            #
            nos = Nos(path)
            exists = nos.dir_exists()
            nonphy = nos.physical_dirs()
            #
            # is not nonphy needed?
            #
            if exists or not nonphy:
                runs = nos.listdir()
                if len(runs) > 0:
                    runs.sort()
                    run = runs[len(runs) - 1]
        results = self.get_named_results_for_run(name=name, run=run)
        if results is not None:
            return results
        #
        # we treat this as a recoverable error because typically the user
        # has complete control of the csvpaths environment, making the
        # problem config that should be addressed.
        #
        # if reached by a reference this error should be trapped at an
        # expression and handled according to the error policy.
        #
        msg = (
            f"Results '{name}' does not exist. Has has that named-paths group been run?"
        )
        self.csvpaths.logger.error(msg)
        if self.csvpaths.ecoms.do_i_raise():
            raise InputException(msg)

    def get_named_results_home(self, name: str) -> str:
        path = os.path.join(self.csvpaths.config.archive_path, name)
        return path

    def get_named_results_for_run(self, *, name: str, run: str) -> list[list[Any]]:
        path = os.path.join(self.csvpaths.config.archive_path, name)
        path = os.path.join(path, run)
        return self._get_named_results_for_run(name=name, run=run, path=path)

    #
    # name = the named-paths / named-results name
    # run = the path to run_dir minus the archive/name root
    # path = the full path to the run_dir
    #
    def _get_named_results_for_run(
        self, *, name: str, run: str, path: str
    ) -> list[list[Any]]:
        instances = Nos(path).listdir()
        rs = [None for inst in instances if inst != "manifest.json"]
        for inst in instances:
            if inst == "manifest.json":
                continue
            r = self.get_named_result_for_instance(
                name=name, run_dir=path, run=run, instance=inst
            )
            rs[r.index] = r
        return rs

    def get_named_result_for_instance(
        self, *, name: str, run_dir: str, run: str, instance: str
    ) -> list[list[Any]]:
        #
        # run_dir is misnamed due to the reimplementation of resreffinder.
        #
        # pre-results ref finder 2 we handled the instances here, but
        # with the new finder we handle names 3 and 4 in the finder where
        # we should be handling everything. for now, the double check here
        # to see if we need to add the instance to the path is fine, but
        # it should be deleted.
        #
        _ = ""

        if run_dir.endswith(f"/{instance}") or run_dir.endswith(f"\\{instance}"):
            instance_dir = run_dir
        else:
            instance_dir = os.path.join(run_dir, instance)
        mani = ResultFileReader.manifest(instance_dir)
        #
        # csvpath needs to be loaded with all meta.json->metadata and some/most of runtime_data
        #
        csvpath = self.csvpaths.csvpath()
        meta = ResultFileReader.meta(instance_dir)
        if meta:
            #
            # until there's a clear case for more, this is all we're going to load.
            # for the most part, people should be using the metadata, not digging into
            # run objects that may not be current. if we really need to recreate the
            # csvpath perfectly we should probably go back and rethink. maybe pickle?
            #
            csvpath.scanner = Scanner(csvpath=csvpath)
            csvpath.scanner.parse(meta["runtime_data"]["scan_part"])
            csvpath.metadata = meta["metadata"]
            csvpath.modes.update()
            csvpath.identity
            csvpath.scan = meta["runtime_data"]["scan_part"]
            csvpath.match = meta["runtime_data"]["match_part"]
            csvpath.delimiter = meta["runtime_data"]["delimiter"]
            csvpath.quotechar = meta["runtime_data"]["quotechar"]
        vars = ResultFileReader.vars(instance_dir)
        if vars:
            csvpath.variables = vars
        #
        # this may not be complete. let's see if it works or needs more.
        #
        # try:
        r = Result(
            csvpath=csvpath,
            paths_name=name,
            run_dir=run_dir,
            file_name=mani["actual_data_file"],
            run_index=mani["instance_index"],
            run_time=dateutil.parser.parse(mani["time"]),
            runtime_data=meta["runtime_data"],
            by_line=not bool(mani["serial"]),
            run_uuid=mani["run_uuid"],
        )
        """
        except Exception as e:
        """
        return r
