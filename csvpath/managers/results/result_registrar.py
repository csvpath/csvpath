import os
import json
from datetime import datetime
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.util.box import Box
from ..listener import Listener
from ..metadata import Metadata
from ..registrar import Registrar
from .result_metadata import ResultMetadata


class ResultRegistrar(Registrar, Listener):
    """@private"""

    def __init__(self, *, csvpaths, result, result_serializer=None):
        Registrar.__init__(self, csvpaths, result)
        Listener.__init__(self, csvpaths.config)
        self.result_serializer = result_serializer
        self.type_name = "result"
        self._nos = None

    @property
    def nos(self) -> Nos:
        if self._nos is None:
            box = Box()
            self._nos = box.get("boto_s3_nos")
            if self._nos is None:
                self._nos = Nos(None)
                box.add("boto_s3_nos", self._nos)
        return self._nos

    def register_start(self, mdata: Metadata) -> None:
        p = self.named_paths_manifest
        mdata.by_line = self.result.by_line
        mdata.run_uuid = self.result.run_uuid
        mdata.manifest_path = self.manifest_path
        mdata.instance_index = self.result.run_index
        mdata.actual_data_file = self.result.actual_data_file
        mdata.origin_data_file = self.result.origin_data_file
        ri = int(self.result.run_index) if self.result.run_index else 0
        if ri >= 1:
            pid = self.csvpaths.paths_manager.get_preceeding_instance_identity(
                self.result.paths_name, ri
            )
            mdata.preceding_instance_identity = pid
        if p is None:
            self.result.csvpath.csvpaths.logger.debug(
                "No named-paths manifest available at %s so not setting named_paths_uuid_string",
                self.named_paths_manifest_path,
            )
        else:
            mdata.named_paths_uuid_string = p["uuid"]
        self.distribute_update(mdata)

    def register_complete(self, mdata: Metadata = None) -> None:
        #
        # results manager delegates the bits to the
        # serializer and the metadata assembly to this
        # registrar, so we expect it to hand us nothing
        # but the result object and serializer.
        #
        m = self.manifest
        if mdata is None:
            mdata = ResultMetadata(config=self.csvpaths.config)
        mdata.from_manifest(m)
        mdata.archive_name = self.archive_name
        mdata.named_results_name = self.result.paths_name
        mdata.named_paths_name = self.result.paths_name
        mdata.named_paths_uuid_string = self.csvpaths.run_metadata.named_paths_uuid
        mdata.named_file_name = self.result.file_name
        mdata.named_file_uuid = self.csvpaths.run_metadata.named_file_uuid
        #
        # exp. swapping for the original above. no negative impact. logically it's the better way.
        #
        mdata.run_dir = self.result.run_dir
        #
        # end exp
        #
        mdata.source_mode_preceding = self.result.source_mode_preceding
        mdata.run_home = self.result.run_dir
        mdata.run_uuid_string = self.csvpaths.run_metadata.run_uuid_string
        mdata.instance_home = self.result.instance_dir
        mdata.instance_identity = self.result.identity_or_index
        mdata.instance_index = self.result.run_index
        mdata.file_fingerprints = self.file_fingerprints
        mdata.error_count = self.result.errors_count
        mdata.valid = self.result.csvpath.is_valid
        mdata.completed = self.completed
        mdata.files_expected = self.all_expected_files
        mdata.number_of_files_expected = len(self.result.csvpath.all_expected_files)
        mdata.number_of_files_generated = self.number_of_files_generated()
        mdata.lines_total = self.result.csvpath.line_monitor.physical_line_count
        mdata.lines_scanned = self.result.csvpath.scan_count
        mdata.lines_matched = self.result.csvpath.match_count
        if self.result.csvpath.transfers:
            tpaths = self.result.csvpath.csvpaths.results_manager.transfer_paths(
                self.result
            )
            mdata.transfers = tpaths
        #
        # input_data_file is deprecated in favor of named_file_name. but atm still used.
        #
        mdata.input_data_file = self.result.file_name
        mdata.actual_data_file = self.result.actual_data_file
        mdata.origin_data_file = self.result.origin_data_file
        ri = int(self.result.run_index) if self.result.run_index else 0
        if ri >= 1:
            pid = self.csvpaths.paths_manager.get_preceeding_instance_identity(
                self.result.paths_name, ri
            )
            mdata.preceding_instance_identity = pid
        self.distribute_update(mdata)

    def metadata_update(self, mdata: Metadata) -> None:
        m = {}
        if mdata.time is None:
            raise ValueError("Time cannot be None")
        m["time"] = mdata.time_string
        m["uuid"] = mdata.uuid_string
        m["serial"] = mdata.by_line is False
        m["archive_name"] = mdata.archive_name
        m["named_results_name"] = mdata.named_results_name
        m["named_paths_uuid"] = mdata.named_paths_uuid_string
        m["run"] = mdata.run
        m["run_uuid"] = mdata.run_uuid_string
        m["run_home"] = mdata.run_home
        m["instance_identity"] = mdata.instance_identity
        m["instance_index"] = mdata.instance_index
        m["instance_home"] = mdata.instance_home
        m["file_fingerprints"] = mdata.file_fingerprints
        m["files_expected"] = mdata.files_expected
        m["number_of_files_expected"] = mdata.number_of_files_expected
        m["number_of_files_generated"] = mdata.number_of_files_generated
        m["valid"] = mdata.valid
        m["completed"] = mdata.completed
        m["source_mode_preceding"] = mdata.source_mode_preceding
        if mdata.source_mode_preceding:
            m["preceding_instance_identity"] = mdata.preceding_instance_identity
        m["actual_data_file"] = mdata.actual_data_file
        m["origin_data_file"] = mdata.origin_data_file
        m["named_file_name"] = mdata.named_file_name
        if mdata.transfers:
            m["transfers"] = mdata.transfers
        mp = self.manifest_path
        m["manifest_path"] = mp
        with DataFileWriter(path=mp) as file:
            json.dump(m, file.sink, indent=2)

    @property
    def archive_name(self) -> str:
        ap = self.result.csvpath.config.archive_path
        nos = self.nos
        nos.path = ap
        sep = nos.sep
        i = ap.rfind(sep)
        if i > 0:
            return ap[i + 1 :]
        return ap

    # gets the manifest for the named_paths as a whole
    @property
    def named_paths_manifest(self) -> dict | None:
        nos = self.nos
        nos.path = self.named_paths_manifest_path
        if nos.exists():
            with DataFileReader(self.named_paths_manifest_path) as file:
                d = json.load(file.source)
                return d
        return None

    # gets the manifest for the named_paths as a whole from the run dir
    @property
    def named_paths_manifest_path(self) -> str:
        return os.path.join(self.result.run_dir, "manifest.json")

    #
    # switch to use ResultManifestReader.manifest
    #
    @property
    def manifest(self) -> dict | None:
        mp = self.manifest_path
        nos = self.nos
        nos.path = mp
        if not nos.exists():
            with DataFileWriter(path=self.manifest_path) as file:
                json.dump({}, file.sink, indent=2)
                return {}
        with DataFileReader(self.manifest_path) as file:
            d = json.load(file.source)
            return d
        return None

    @property
    def manifest_path(self) -> str:
        h = os.path.join(self.result_path, "manifest.json")
        return h

    @property
    def result_path(self) -> str:
        rdir = self.result_serializer.get_instance_dir(
            run_dir=self.result.run_dir, identity=self.result.identity_or_index
        )
        nos = self.nos
        nos.path = rdir
        if not nos.exists():
            nos.makedir()
        return rdir

    @property
    def completed(self) -> bool:
        return self.result.csvpath.completed

    @property
    def all_expected_files(self) -> bool:
        #
        # True if the files in files-mode are all present. we can have more than those
        # listed files, but if we're missing any that are listed we return False.
        #
        # we can not have any/all of data.csv, unmatched.csv, and printouts.txt without
        # it necessarily being a failure mode. but we can require them as a matter of
        # content validation.
        #
        if (
            self.result.csvpath.all_expected_files is None
            or len(self.result.csvpath.all_expected_files) == 0
        ):
            if not self.has_file("meta.json"):
                return False
            if not self.has_file("errors.json"):
                return False
            if not self.has_file("vars.json"):
                return False
            return True
        for t in self.result.csvpath.all_expected_files:
            t = t.strip()
            if t.startswith("no-data"):
                if self.has_file("data.csv"):
                    return False
            if t.startswith("data") or t.startswith("all"):
                if not self.has_file("data.csv"):
                    return False
            if t.startswith("no-unmatched"):
                if self.has_file("unmatched.csv"):
                    return False
            if t.startswith("unmatched") or t.startswith("all"):
                if not self.has_file("unmatched.csv"):
                    return False
            if t.startswith("no-printouts"):
                if self.has_file("printouts.txt"):
                    return False
            if t.startswith("printouts") or t.startswith("all"):
                if not self.has_file("printouts.txt"):
                    return False
            if not self.has_file("meta.json"):
                return False
            if not self.has_file("errors.json"):
                return False
            if not self.has_file("vars.json"):
                return False
        return True

    def number_of_files_generated(self) -> int:
        n = 0
        n += 1 if self.has_file("meta.json") else 0
        n += 1 if self.has_file("errors.json") else 0
        n += 1 if self.has_file("vars.json") else 0
        n += 1 if self.has_file("data.csv") else 0
        n += 1 if self.has_file("unmatched.csv") else 0
        n += 1 if self.has_file("printouts.txt") else 0
        return n

    def has_file(self, t: str) -> bool:
        r = self.result_path
        nos = self.nos
        nos.path = os.path.join(r, t)
        return nos.exists()

    @property
    def file_fingerprints(self) -> dict[str]:
        r = self.result_path
        fps = {}
        for t in [
            "data.csv",
            "meta.json",
            "unmatched.csv",
            "printouts.txt",
            "errors.json",
            "vars.json",
        ]:
            f = self._fingerprint(os.path.join(r, t))
            if f is None:
                continue
            fps[t] = f
        return fps

    def _fingerprint(self, path) -> str:
        if path.find("://") == -1 and not path.startswith("/"):
            path = f"{os.getcwd()}/{path}"
        nos = self.nos
        nos.path = path
        if nos.exists():
            with DataFileReader(path) as f:
                h = f.fingerprint()
                return h
        return None
