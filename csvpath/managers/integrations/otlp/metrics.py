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

    def _get(self, *, name: str, section: str = None) -> str:
        if name is None:
            raise ValueError("Name cannot be None")
        #
        # we expect people to usually config OTLP using env vars. however,
        # in some cases env var substitution may be configured to look at env.json
        # rather than the OS env vars.
        #
        # in the case of FlightPath Server, FlightPath Data may copy OS env vars
        # into the serverside env.json, potentially leaving out of config.ini and
        # just act similar to how the OS env vars configure OTLP in the background.
        #
        # sounds complicated, but imagine the user sets the OS env vars, configs
        # their FlightPath Server project, pushes it to FPS and FlightPath Data
        # either transparently or through a form copies OS env vars when the proj
        # config is pushed. that would be simpler for the user. and it keeps them
        # from having to put the info in the config.ini as values (not ideal
        # security) or OS env var pointers (requiring double entry and/or a change
        # when the project config is pushed to FPS).
        #
        c = self._csvpaths.config
        ret = c.get(section=section, name=name)
        if ret is None:
            self._csvpaths.logger.warning(
                f"No OTLP config value found for [{section}] {name} in config.ini or env.json"
            )
        return ret
        #
        # moved this into Config
        #
        """
        ret = None
            if section is not None:
                try:
                    ret = c.get(section=section, name=name)
                except Exception:
                    ...
            if ret is None:
                ret = c.config_env.get(name=name)
            if ret is None:
                self._csvpaths.logger.warning(f"No OTLP config value found for [{section}] {name} in config.ini or env.json")
            return ret
        """

    @property
    def provider(self) -> LoggerProvider:
        if self._provider is None:
            try:
                # Add resource information
                resource = Resource.create(
                    {"service.name": "CsvPath", "service.version": "1.0.0"}
                )
                self._provider = LoggerProvider(resource=resource)
                set_logger_provider(self._provider)
                #
                # these were working values for a local openobserve.
                #
                # OTEL_EXPORTER_OTLP_ENDPOINT=http://0.0.0.0:5080/api/default/v1/logs
                # OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic ZGsxMDdka0Bob3RtYWlsLmNvbTpoYW5nemhvdQ==,stream-name=flightpath
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
                # because we plan to allow projects to push data to their own choice of OTLP
                # platform. FlightPath Data will have to provide an API for setting env.json
                # and assistence in copying its own env vars and the OS env vars to env.json
                # on the server.
                #
                endpoint = self._get(name="OTEL_EXPORTER_OTLP_LOGS_ENDPOINT")
                if endpoint is None or endpoint == "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT":
                    endpoint = self._get(name="OTEL_EXPORTER_OTLP_ENDPOINT")
                if endpoint is None or endpoint == "OTEL_EXPORTER_OTLP_ENDPOINT":
                    raise ValueError(
                        "You must pass either OTEL_EXPORTER_OTLP_ENDPOINT or OTEL_EXPORTER_OTLP_LOGS_ENDPOINT, the latter preferred"
                    )
                headers = self._get(name="OTEL_EXPORTER_OTLP_HEADERS")
                if headers is None or headers == "OTEL_EXPORTER_OTLP_HEADERS":
                    raise ValueError("OTEL_EXPORTER_OTLP_HEADERS cannot be None")
                headers = headers.split(",")
                d = {}
                for _ in headers:
                    k = _[0 : _.find("=")]
                    v = _[_.find("=") + 1 :]
                    d[k] = v
                exporter = OTLPLogExporter(endpoint=endpoint, headers=d)
                self._provider.add_log_record_processor(
                    BatchLogRecordProcessor(exporter)
                )
            except Exception as ex:
                if self._csvpaths:
                    self._csvpaths.logger.error("Cannot configure OTLP")
                    self._csvpaths.logger.error(ex)
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
            # logging.basicConfig(level=logging.DEBUG)
        return logger
