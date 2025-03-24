import os
import json
from datetime import datetime, timezone
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.references.files_reference_finder import FilesReferenceFinder
from csvpath.util.references.results_reference_finder import ResultsReferenceFinder
from csvpath.util.exceptions import CsvPathsException
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.file_readers import DataFileReader
from csvpath.util.template_util import TemplateUtility as temu


class RunHomeMaker:
    """
    Makes the run directory name for a CsvPaths run. (collect, fast_forward, next).
    run home (a.k.a. run_dir) are datetime strings in the form 2025-03-11_18-50-56_1.
    the run method caller can provide a template in the form ":1/:2/:run_dir/:4" to
    make a custom tree in the archive. we would advise only doing that if there is a
    compelling reason; otherwise, just keep things simple and consistent. The :1, :2,
    etc. tokens refer to the parts of the original file path. if you have a file that
    arrives at:
        a/b/c/d/e.csv
    and a template like:
        :2/:3/:run_dir/:1
    you get a directory path of:
        archive_root/c/d/2025-03-11_18-50-56_1/b
    with results files like:
        archive_root/c/d/2025-03-11_18-50-56_1/b/data.csv
        archive_root/c/d/2025-03-11_18-50-56_1/b/vars.json
        archive_root/c/d/2025-03-11_18-50-56_1/b/printouts.txt
        archive_root/c/d/2025-03-11_18-50-56_1/b/...
    """

    def __init__(self, csvpaths) -> None:
        self._csvpaths = csvpaths
        self.base_dir = csvpaths.config.archive_path

    #
    # runs_home is the parent dir of the run_dirs. e.g. in: archive/food/2025-03.../categories
    # the runs_home is archive/food. in archive/food/above/2025-03.../below/categories the runs_home is
    # archive/food/above
    #
    """
    def runs_home_from_template(self, pathsname: str) -> str:
        #
        # go to the paths group and find the template
        #
        mani = self._csvpaths.paths_manager.get_manifest_for_name(pathsname)
        if mani is None:
            raise RuntimeError(f"Manifest for {pathsname} cannot be None")
        template = mani.get("template")
        if template is None:
            return self._csvpaths.paths_manager.named_paths_home(pathsname)
        #
        #
        #
        self.results_dir_name(pathsname, filename, run_dir, template)
    """
    #
    # this method isn't needed but it is used.
    #
    def run_time_str(self, pathsname=None, filename=None) -> str:
        #
        # this method and get_run_dir have to work on a full dir path because we
        # have to make sure the dir name is not taken. if/when we want to operate
        # on just the directory name itself we have to pop it off the list of path
        # parts.
        #
        if self._csvpaths._run_time_str is None and pathsname is None:
            raise CsvPathsException(
                "Cannot have None in both run_time_str and pathsname"
            )
        return self.get_run_dir(paths_name=pathsname, file_name=filename)

    """
    #
    # this method may not be needed if it was only used by csvpaths to get the run dir.
    #
    def results_dir_path(
        self, *, pathsname: str, filename: str, run_dir: str, template: str
    ) -> str:
        #
        # this method calls results_dir_name
        #
        if template is None or template == ":run_dir":
            return run_dir
        parts = pathu.parts(run_dir)
        d = self.results_dir_name(
            pathsname=pathsname, filename=filename, run_dir=parts[2], template=template
        )
        parts[2] = d
        path = f"{os.sep}".join(parts)
        self._csvpaths.logger.debug(
            f"RunHomeMaker: results_dir_path: pathsname: {pathsname}"
        )
        self._csvpaths.logger.debug(f"RunHomeMaker: filename: {filename}")
        self._csvpaths.logger.debug(f"RunHomeMaker: run_dir: {run_dir}")
        self._csvpaths.logger.debug(f"RunHomeMaker: template: {template}")
        self._csvpaths.logger.debug(f"RunHomeMaker: parts: {parts}")
        self._csvpaths.logger.debug(f"RunHomeMaker: path: {path}")
        return path
    """

    def results_dir_name(
        self, *, pathsname: str, filename: str, run_dir: str, template: str
    ) -> str:
        #
        # if we have path extensions they go here. a path template organizes the
        # dir structure of the archive more intentionally. it could look like:
        #
        #    ":1/:2/:run_dir/:4"
        #
        # :1, :2, :4 refer to path segments of the location of the original file.
        # that is the "from" key in the named-file's manifest
        #
        # :run_dir is the run time string we just created above; the run's run home
        # directory.
        #
        self._csvpaths.logger.debug(
            f"RunHomeMaker: results_dir_name: pathsname: {pathsname}"
        )
        self._csvpaths.logger.debug(
            f"RunHomeMaker: results_dir_name: filename: {filename}"
        )
        self._csvpaths.logger.debug(
            f"RunHomeMaker: results_dir_name: run_dir: {run_dir}"
        )
        self._csvpaths.logger.debug(
            f"RunHomeMaker: results_dir_name: template: {template}"
        )
        rts = self.run_time_str(pathsname, filename)
        rts = self.get_run_dir(paths_name=pathsname, file_name=filename)
        if template is None:
            return rts
        if template.find(":run_dir") == -1:
            raise ValueError("Path template must include :run_dir")
        #
        # find all the path parts from the original filename
        #
        path = self.get_data_file_path(filename)
        parts = pathu.parts(path)
        for i, p in enumerate(parts):
            template = template.replace(f":{i}", p)
        template = template.replace(":run_dir", run_dir)
        return template

    def get_data_file_path(self, filename: str) -> str:
        if filename.startswith("$"):
            #
            # plain named-file name
            #
            mani = self._csvpaths.file_manager.get_manifest(filename)
            ref = ReferenceParser(filename)
            datatype = ref.datatype
            if datatype == ReferenceParser.RESULTS:
                if ref.name_three is None:
                    #
                    # if we're getting the run manifest we need: named_file_path
                    #
                    # this cannot work. the method was moved to results_reference_finder
                    # and it returns a dir, not a manifest and we are not adding "manifest.json"
                    # to the path here. there must be no test and may be no use case. :/
                    #
                    raise RuntimeError(
                        "Unexpected branch in reference parsing. Expecting 'abc' as in $*.results.*.abc"
                    )
                else:
                    #
                    # if we're getting an instance manifest we need: origin_data_file
                    # we take the original name because it has meaning for the purposes of
                    # structuring the results in the archive; whereas, a source-mode:preceding
                    # data.csv file doesn't have that meaningfulness.
                    #
                    refinder = ResultsReferenceFinder(self._csvpaths, name=filename)
                    mpath = refinder.resolve(filename)
                    mpath = os.path.join(mpath, "manifest.json")
                    nos = Nos(mpath)
                    if nos.exists():
                        with DataFileReader(mpath) as file:
                            mani = json.load(file.source)
                            path = mani["origin_data_file"]
            elif datatype == ReferenceParser.FILES:
                #
                # need "from" of the version of the named-file pointed to by the reference.
                #
                finder = FilesReferenceFinder(self._csvpaths, ref=ref)
                mani = finder.manifest
                index = finder.version_index
                path = mani[index]["from"]
            else:
                raise ValueError("Unhandled reference type in {filename}")
        else:
            #
            # plain named-file name
            #
            mani = self._csvpaths.file_manager.get_manifest(filename)
            path = mani[len(mani) - 1]["from"]
        if path is None:
            raise ValueError("Cannot find path of data file for {filename}")
        return path

    @property
    def current_run_time(self) -> datetime:
        """@private
        gets the time marking the start of the run. used to create the run home directory."""
        if self._csvpaths._current_run_time is None:
            self._csvpaths._current_run_time = datetime.now(timezone.utc)
        return self._csvpaths._current_run_time

    # ==============================================
    # brought over from ResultSerializer
    # ==============================================

    def _deref_paths_name(self, paths_name) -> str:
        #
        # if we have a reference we need to de-ref so that our path has only
        # the named-paths name at the top, not the $, datatype, etc.
        #
        paths_name = paths_name.lstrip("$")
        i = paths_name.find(".")
        if i > -1:
            paths_name = paths_name[0:i]
        i = paths_name.find("#")
        if i > -1:
            paths_name = paths_name[0:i]
        return paths_name

    """
    def get_run_dir_name_from_datetime(self, dt) -> str:
        #
        # called by get_run_dir
        #
        if dt is None:
            return None
        t = dt.strftime("%Y-%m-%d_%H-%M-%S")
        return t
    """

    #
    # this is the method csvpaths uses to site a run.
    #
    def get_run_dir(self, paths_name: str, file_name: str, template: str = "") -> str:
        if self._csvpaths._run_time_str is not None:
            return self._csvpaths._run_time_str
        #
        # run_dir not needed. we can create the time str ourselves.
        #
        # get the name of the named paths-name (could be a reference)
        # get the filename by from file mgr and/or ReferenceFinder (which file mgr should be using?)
        # build the prefix
        # test prefix+time dirs till one fits
        # add the suffix
        # return it
        #
        run_time = self._csvpaths.current_run_time
        if run_time is None:
            run_time = datetime.now()
        if not isinstance(run_time, str):
            run_time = run_time.strftime("%Y-%m-%d_%H-%M-%S")
            # run_time = self.get_run_dir_name_from_datetime(run_time)
        #
        # get the pathsname
        #
        print(f"humemakr: get_run_dir: paths_name: {paths_name}")
        print(f"humemakr: get_run_dir: file_name: {file_name}")

        if paths_name.startswith("$"):
            ref = ReferenceParser(paths_name)
            paths_name = ref.root_major
        file = None
        #
        # get the origin file path. we use the original location of the file
        # to construct the template-based results path. both the file and the paths
        # templates look at the source location. the origin file is still used even
        # when the reference is to a result data file, not to a named-file.
        #

        if file_name.startswith("$"):
            ref = ReferenceParser(file_name)
            if ref.datatype == ref.FILES:
                mani = FilesReferenceFinder(
                    self._csvpaths, ref=ref
                ).get_manifest_entry_for_reference()
            elif ref.datatype == ref.RESULTS:
                mani = ResultsReferenceFinder(
                    self._csvpaths, name=file_name
                ).get_file_manifest_entry_for_results_reference()
            file = mani["from"]
        else:
            mani = self._csvpaths.file_manager.get_manifest(file_name)
            for _ in mani:
                print(f"humemakr: get_run_dir: _: {_}")
            file = mani[len(mani) - 1]["from"]

        print(f"humemakr: get_run_dir: file: {file}")

        #
        # needed here?
        # file = pathu.resep(file)
        #
        if isinstance(file, list):
            file = file[0]
        suffix = ""
        prefix = ""
        if template is not None and template.strip() != "":
            if not temu.valid(template):
                raise ValueError(f"Invalid template: {template}")
            suffix = temu.get_template_suffix(template=template)
            i = template.find(":run_dir")
            prefix = template[0:i]
            print(f"humemakr: get_run_dir: prefix 1: {prefix}")
            parts = pathu.parts(file)
            print(f"humemakr: get_run_dir: parts: {parts}")
            for i, p in enumerate(parts):
                prefix = prefix.replace(f":{i}", p)
            print(f"humemakr: get_run_dir: prefix 2: {prefix}")
            prefix = pathu.resep(prefix)
            print(f"humemakr: get_run_dir: prefix 2.5: {prefix}")
        #
        # TODO: check for an assure_paths_home type method in paths mgr
        #
        run_dir = os.path.join(self.base_dir, paths_name)
        print(f"humemakr: get_run_dir: run_dir 1: {run_dir}")
        nos = Nos(run_dir)
        if not nos.dir_exists():
            nos.makedirs()
        run_dir = os.path.join(run_dir, f"{prefix}{run_time}")
        #
        print(f"humemakr: get_run_dir: run_dir 2: {run_dir}")
        #
        # the path existing for a different named-paths run in progress
        # or having completed less than 1000ms ago. CsvPaths are single-user,
        # single-use. a server process would namespace each CsvPaths instance
        # to prevent conflicts. if there is a conflict the two runs would
        # overwrite each other locally. this prevents that.
        #
        nos.path = run_dir
        if nos.dir_exists():
            i = 0
            adir = f"{run_dir}_{i}"
            nos.path = adir
            while True:
                nos.path = adir
                if nos.dir_exists():
                    i += 1
                    adir = f"{run_dir}_{i}"
                else:
                    break
            run_dir = adir
            #
            # this still leaves a race condition to be addressed for non-local. to be addressed with api/db.
            #
            nos.path = run_dir
            nos.makedirs()
            #
            #
            #
        run_dir = f"{run_dir}{suffix}"
        print(f"humemakr: get_run_dir: run_dir 3: {run_dir}")
        self._csvpaths._run_time_str = run_dir
        return self._csvpaths._run_time_str
