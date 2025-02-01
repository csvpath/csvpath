from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_registrar import ResultsRegistrar
from .otlp_listener import OtlpListener
from .metrics import Metrics


class OpenTelemetryResultListener(OtlpListener):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.csvpaths = None
        self.result = None

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError(
                "OTLP listener cannot continue without a CsvPaths instance"
            )
        if self.csvpaths.metrics is None:
            self.csvpaths.metrics = Metrics(self)
        if mdata.error_count:
            self.csvpaths.metrics.errors.add(mdata.error_count, self.core_meta(mdata))
        if mdata.valid:
            v = 0
            if mdata.valid is True:
                v = 1
            self.csvpaths.metrics.valid.add(v, self.core_meta(mdata))
        if mdata.file_count:
            self.csvpaths.metrics.files.add(mdata.file_count, self.core_meta(mdata))
        yn = mdata.files_expected
        if yn and not isinstance(yn, bool):
            raise ValueError("Files expected must convert to bool")
        if yn is True:
            yn = 1
        else:
            yn = 0
        self.csvpaths.metrics.files_expected.add(yn, self.core_meta(mdata))

    def core_meta(self, mdata):
        cmeta = super().core_meta(mdata)
        if mdata.instance_identity:
            cmeta["instance"] = mdata.instance_identity
        #
        # named_paths_uuid_string should be on results as well
        #
        if mdata.named_paths_uuid_string:
            cmeta["named_paths_uuid_string"] = mdata.named_paths_uuid_string
        return cmeta
