import logging
import traceback
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from .otlp_listener import OtlpListener

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


class OpenTelemetryPathsListener(OtlpListener):
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
            ids = []
            #
            # otlp doesn't like Nones. should there not be any?
            #
            for _ in mdata.named_paths_identities:
                if _:
                    ids.append(_)
            etype = "named-paths group load"
            extra = {
                "event_type": etype,
                "event_listener": "paths",
                "named_paths_name": mdata.named_paths_name,
                "named_paths_home": mdata.named_paths_home,
                "group_file_path": mdata.group_file_path,
                "named_paths_count": mdata.named_paths_count,
                "named_paths_identities": ids,
                "source_path": mdata.source_path,
                "template": mdata.template if mdata.template else "",
                **self.core_meta(mdata),
            }
            self.csvpaths.__class__.METRICS.logger().debug(
                "Csvpath completed", extra=extra
            )
        except Exception as ex:
            print(traceback.format_exc())
            self.csvpaths.logger.error(ex)
