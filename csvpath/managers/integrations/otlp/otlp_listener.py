from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_registrar import ResultsRegistrar
from .metrics import Metrics


class OtlpListener(Listener):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.csvpaths = None
        self.result = None

    def core_meta(self, mdata: Metadata) -> dict:
        cmeta = {}
        if mdata.named_file_name:
            cmeta["file"] = mdata.named_file_name
        if mdata.named_results_name:
            cmeta["paths"] = mdata.named_results_name
        if mdata.archive_name:
            cmeta["archive"] = mdata.archive_name
        if mdata.archive_path:
            cmeta["archive_path"] = mdata.archive_path
        if mdata.named_files_root:
            cmeta["named_files_root"] = mdata.named_files_root
        if mdata.named_paths_root:
            cmeta["named_paths_root"] = mdata.named_paths_root
        if mdata.uuid_string:
            cmeta["uuid"] = mdata.uuid_string
        if mdata.run_home:
            cmeta["run_home"] = mdata.run_home
        if mdata.hostname:
            cmeta["hostname"] = mdata.hostname
        if mdata.username:
            cmeta["username"] = mdata.username
        if mdata.ip_address:
            cmeta["ip_address"] = mdata.ip_address

        return cmeta
