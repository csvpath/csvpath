import logging
import traceback

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from .otlp_listener import OtlpListener
from .metrics import Metrics


class OpenTelemetryResultListener(OtlpListener):
    def __init__(self, config=None):
        super().__init__()
        self.csvpaths = None
        self.result = None

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError(
                "OTLP listener cannot continue without a CsvPaths instance"
            )
        self.assure_metrics()
        try:
            etype = (
                "csvpath run result" if mdata.time_completed else "csvpath run start"
            )
            extra = {
                "event_type": etype,
                "event_listener": "result",
                "error_count": mdata.error_count,
                "valid": bool(mdata.valid) if mdata is not None else "",
                "files_generated": mdata.number_of_files_generated,
                "files_expected": bool(mdata.files_expected),
                **self.core_meta(mdata),
            }
            self.csvpaths.__class__.METRICS.logger().debug(
                "Csvpath completed", extra=extra
            )
        except Exception as ex:
            print(traceback.format_exc())
            self.csvpath.logger.error(ex)

    def core_meta(self, mdata):
        cmeta = super().core_meta(mdata)
        if mdata.time_completed:
            cmeta["time_completed"] = mdata.time_completed_string
        if mdata.instance_identity:
            cmeta["instance"] = mdata.instance_identity
        if mdata.named_paths_uuid_string:
            cmeta["named_paths_uuid_string"] = mdata.named_paths_uuid_string
        return cmeta
