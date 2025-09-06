import math
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from csvpath.managers.listener import Listener


class ErrorMetrics:
    def __init__(self, listener: Listener, exporting=True):
        ...
