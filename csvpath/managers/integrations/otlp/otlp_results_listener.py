from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_registrar import ResultsRegistrar
from .otlp_listener import OtlpListener
from .metrics import Metrics


class OpenTelemetryResultsListener(OtlpListener):
    def __init__(self, config=None):
        super().__init__(config=config)
        self.csvpaths = None

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError(
                "OTLP listener cannot continue without a CsvPaths instance"
            )
        if self.csvpaths.metrics is None:
            self.csvpaths.metrics = Metrics(self)
        if mdata.status == ResultsRegistrar.COMPLETE:
            self.csvpaths.metrics.runs_completed.add(1, self.core_meta(mdata))
        else:
            self.csvpaths.metrics.runs_started.add(1, self.core_meta(mdata))
        size = mdata.named_file_size
        if size:
            try:
                size = int(size)
            except ValueError:
                size = None
        if size is not None:
            self.csvpaths.metrics.bytes.add(size, self.core_meta(mdata))
            self.csvpaths.metrics.size.record(size, self.core_meta(mdata))
