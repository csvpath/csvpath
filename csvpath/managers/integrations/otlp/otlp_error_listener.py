from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_registrar import ResultsRegistrar
from .otlp_listener import OtlpListener
from .error_metrics import ErrorMetrics


class OpenTelemetryErrorListener(OtlpListener):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.csvpaths = None
        self.csvpath = None

    def assure_metrics(self) -> None:
        metrics = None
        if self.csvpaths and self.csvpaths.error_manager.error_metrics is None:
            if metrics is None:
                metrics = ErrorMetrics(self)
            self.csvpaths.error_manager.error_metrics = metrics
        if self.csvpath and self.csvpath.error_manager.error_metrics is None:
            if not metrics:
                metrics = ErrorMetrics(self)
            self.csvpath.error_manager.error_metrics = metrics

    def error_meta(self, mdata: Metadata) -> dict:
        emeta = {}
        if mdata.archive_name:
            emeta["archive_name"] = mdata.archive_name
        if mdata.archive_path:
            emeta["archive_path"] = mdata.archive_path
        if mdata.named_files_root:
            emeta["named_files_root"] = mdata.named_files_root
        if mdata.named_paths_root:
            emeta["named_paths_root"] = mdata.named_paths_root
        if mdata.uuid_string:
            emeta["uuid"] = mdata.uuid_string
        if mdata.named_file_name:
            emeta["named_file_name"] = mdata.named_file_name
        if mdata.named_paths_name:
            emeta["named_paths_name"] = mdata.named_paths_name
        if mdata.identity:
            emeta["identity"] = mdata.identity
        if mdata.filename:
            emeta["filename"] = mdata.filename
        if mdata.line_count:
            emeta["line_count"] = mdata.line_count
        if mdata.source:
            emeta["source"] = mdata.source
        if mdata.message:
            emeta["message"] = mdata.message
        if mdata.hostname:
            emeta["hostname"] = mdata.hostname
        if mdata.cwd:
            emeta["cwd"] = mdata.cwd
        if mdata.pid:
            emeta["pid"] = mdata.pid
        if mdata.username:
            emeta["username"] = mdata.username
        if mdata.ip_address:
            emeta["ip_address"] = mdata.ip_address

        return emeta

    def metadata_update(self, mdata: Metadata) -> None:
        self.assure_metrics()
        self.csvpaths.error_manager.error_metrics.error_events.add(
            1, self.error_meta(mdata)
        )
