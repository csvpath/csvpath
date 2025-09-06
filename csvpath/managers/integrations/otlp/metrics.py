import logging
from logging import Logger
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


class Metrics:

    LOGGERS: dict[str, Logger] = {}

    def __init__(self):
        self._provider: LoggerProvider = None

    @property
    def provider(self) -> LoggerProvider:
        if self._provider is None:
            # Add resource information
            resource = Resource.create(
                {"service.name": "CsvPath", "service.version": "1.0.0"}
            )
            self._provider = LoggerProvider(resource=resource)
            set_logger_provider(self._provider)
            exporter = OTLPLogExporter()
            """
            #
            # we may need to allow for programmatic set of endpoint for FlightPath Server
            #
            exporter = OTLPLogExporter(
                endpoint="http://localhost:5080/api/default/v1/logs"  # More specific endpoint
            )
            """
            self._provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        return self._provider

    def logger(self, project: str = "csvpath") -> Logger:
        logger = Metrics.LOGGERS.get(project)
        if logger is None:
            #
            # we want the logging handler to accept anything. the logger may be
            # (re)set to a higher level to filter down what it sends to the handler.
            # caution, tho, not 100% that works as advertised yet.
            #
            handler = LoggingHandler(level=logging.DEBUG, logger_provider=self.provider)
            logger = logging.getLogger(f"{project}.otlp")
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            # Prevent propagation to avoid duplicate logs
            logger.propagate = False
            Metrics.LOGGERS[project] = logger
        return logger
