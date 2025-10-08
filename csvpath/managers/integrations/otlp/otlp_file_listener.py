import logging
import traceback
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from .otlp_listener import OtlpListener

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


class OpenTelemetryFileListener(OtlpListener):
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
            extra = {
                "event_type": "named-file add",
                "event_listener": "file",
                "named_file_name": mdata.named_file_name,
                "named_file_home": mdata.name_home,
                "origin_path": mdata.origin_path,
                "file_home": mdata.file_home,
                "file_path": mdata.file_path,
                "file_name": mdata.file_name,
                "file_type": mdata.type,
                "file_mark": mdata.mark,
                "file_size": mdata.file_size,
                "template": mdata.template if mdata.template else "",
                **self.core_meta(mdata),
            }
            self.csvpaths.__class__.METRICS.logger().debug("File added", extra=extra)
        except Exception as ex:
            print(traceback.format_exc())
            self.csvpaths.logger.error(ex)
