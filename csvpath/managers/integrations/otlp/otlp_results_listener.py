import logging
import traceback
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from .otlp_listener import OtlpListener

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


class OpenTelemetryResultsListener(OtlpListener):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.csvpaths = None

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError(
                "OTLP listener cannot continue without a CsvPaths instance"
            )
        self.assure_metrics()
        try:
            etype = (
                "named-paths group run result"
                if mdata.time_completed
                else "named-paths group run start"
            )
            extra = {
                "event_type": etype,
                "event_listener": "results",
                "named_results_name": mdata.named_results_name,
                "named_file_uuid": mdata.named_file_uuid,
                "named_file_name": mdata.named_file_name,
                "named_file_path": mdata.named_file_path,
                "named_file_fingerprint": mdata.named_file_fingerprint,
                "named_file_fingerprint_on_file": mdata.named_file_fingerprint_on_file,
                "named_file_size": mdata.named_file_size,
                "named_file_last_change": mdata.named_file_last_change,
                "status": mdata.status,
                "all_completed": mdata.all_completed,
                "all_valid": mdata.all_valid,
                "error_count": mdata.error_count,
                "all_expected_files": mdata.all_expected_files,
                "by_line": mdata.by_line,
                "_run_uuid": mdata._run_uuid,
                **self.core_meta(mdata),
            }
            self.csvpaths.__class__.METRICS.logger().debug(
                "Csvpath completed", extra=extra
            )
        except Exception as ex:
            print(traceback.format_exc())
            self.csvpaths.logger.error(ex)

    def core_meta(self, mdata):
        cmeta = super().core_meta(mdata)
        if mdata.time_completed:
            cmeta["time_completed"] = mdata.time_completed_string
        if mdata.named_paths_uuid_string:
            cmeta["named_paths_uuid_string"] = mdata.named_paths_uuid_string
        return cmeta
