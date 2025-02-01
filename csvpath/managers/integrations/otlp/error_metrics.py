from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from csvpath.managers.listener import Listener


class ErrorMetrics:
    def __init__(self, listener: Listener, exporting=True):
        self.listener = listener
        self.reader = None
        self.provider = None
        self.meter = None
        if exporting:
            self.reader = PeriodicExportingMetricReader(OTLPMetricExporter())
            self.provider = MeterProvider(metric_readers=[self.reader])
            metrics.set_meter_provider(self.provider)
        else:
            self.reader = InMemoryMetricReader()
            self.provider = MeterProvider(metric_readers=[self.reader])
            metrics.set_meter_provider(self.provider)

        self.meter = metrics.get_meter("runtime_errors")

        self.error_events = self.meter.create_counter(
            "runtime_errors",
            description="Error events during a csvpath run or a csvpaths load",
        )
