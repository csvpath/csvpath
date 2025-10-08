from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.integrations.otlp.metrics import Metrics


class OtlpListener(Listener):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.csvpaths = None
        self.result = None

    def assure_metrics(self) -> Metrics:
        if self.csvpaths is None:
            raise RuntimeError("There must be a CsvPaths instance")
        if self.csvpaths.__class__.METRICS is None:
            self.csvpaths.__class__.METRICS = Metrics(self.csvpaths)
        return self.csvpaths.__class__.METRICS

    def core_meta(self, mdata: Metadata) -> dict:
        cmeta = {}
        cmeta["time"] = mdata.time_string
        #
        # project_context is a grouper that will hold the API key hash for
        # flightpath server. other users can use it other ways as needed.
        #
        cmeta["project_context"] = self.csvpaths.project_context
        cmeta["project"] = self.csvpaths.project

        if hasattr(mdata, "named_file_name"):
            cmeta["file"] = mdata.named_file_name
        if hasattr(mdata, "named_results_name"):
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
        if hasattr(mdata, "run_home"):
            cmeta["run_home"] = mdata.run_home
        if mdata.hostname:
            cmeta["hostname"] = mdata.hostname
        if mdata.username:
            cmeta["username"] = mdata.username
        if mdata.ip_address:
            cmeta["ip_address"] = mdata.ip_address

        return cmeta
