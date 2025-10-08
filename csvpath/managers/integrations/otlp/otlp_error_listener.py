import logging
import traceback
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from .otlp_listener import OtlpListener


class OpenTelemetryErrorListener(OtlpListener):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.csvpaths = None
        self.csvpath = None

    def error_meta(self, mdata: Metadata) -> dict:
        emeta = {}
        emeta["event_type"] = "error"
        emeta["event_listener"] = "error"
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
        if self.csvpaths:
            self.assure_metrics()
        else:
            return
        try:
            emeta = self.error_meta(mdata)
            msg = emeta.get("message")
            if msg is None or msg.strip() == "":
                msg = "Unknown error"
            self.csvpaths.__class__.METRICS.logger().debug(msg, extra=emeta)
        except Exception as ex:
            print(traceback.format_exc())
            self.csvpath.logger.error(ex)
