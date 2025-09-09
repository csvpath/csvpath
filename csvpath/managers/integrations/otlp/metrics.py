import logging
from logging import Logger
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.resources import Resource
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


class Metrics:

    LOGGERS: dict[str, Logger] = {}

    def __init__(self, csvpaths):
        self._provider: LoggerProvider = None
        if csvpaths is None:
            raise ValueError("Csvpaths cannot be None")
        self._csvpaths = csvpaths

    def _get(self, *, key: str, section: str = None) -> str:
        if key is None:
            raise ValueError("Key cannot be None")
        c = self._csvpaths.config
        ret = None
        if section is not None:
            try:
                ret = c.get(section=section, name=key)
            except Exception:
                ...
        if ret is None:
            ret = c.config_env.get(name=key)
        return ret

    @property
    def provider(self) -> LoggerProvider:
        if self._provider is None:
            # Add resource information
            resource = Resource.create(
                {"service.name": "CsvPath", "service.version": "1.0.0"}
            )
            self._provider = LoggerProvider(resource=resource)
            set_logger_provider(self._provider)

            # endpoint=None, certificate_file=None, client_key_file=None, client_certificate_file=None, headers=None, timeout=None, compression=None, session=None

            endpoint = self._get()
            #
            # these were working values for openobserve. I don't think we need
            # OTEL_EXPORTER_OTLP_PROTOCOL  since we are programmatically instantiating
            # the protobuf
            #
            # OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
            # OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:5080/api/default
            # OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic ZGsxMDdka0Bob3RtYWlsLmNvbTpoYW5nemhvdQ==,stream-name=FlightPath
            #
            # certificate_file=None,
            # client_key_file=None,
            # client_certificate_file=None,
            # timeout=None,
            # compression=None,
            # session=None
            #
            # in CsvPath and FlightPath Data these can come from regular env vars
            # but in FlightPath Server they must come from var_sub_source=config/env.json
            # because we plan to allow projects to push data to their own choice of OTLLP
            # platform. FlightPath Data will have to provide an API for setting env.json
            # and assistence in copying its own env vars and the OS env vars to env.json
            # on the server.
            #
            endpoint = self._get("OTEL_EXPORTER_OTLP_ENDPOINT")
            headers = self._get("OTEL_EXPORTER_OTLP_HEADERS")
            exporter = OTLPLogExporter(endpoint=endpoint, headers=headers)
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
