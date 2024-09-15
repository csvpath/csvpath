import traceback
from logging.handlers import RotatingFileHandler
import logging


class LogException(Exception):
    pass


class LogUtility:
    LOGGERS = {}

    @classmethod
    def log_brief_trace(cls, logger=None) -> str:
        trace = "".join(traceback.format_stack())
        i = 13
        lines = trace.split("\n")
        ret = ""
        while i > 0:
            i = i - 1
            aline = lines[len(lines) - i - 1]
            aline = aline.strip()
            if aline[0:4] != "File":
                continue
            if not logger:
                print(f"{aline}")
            else:
                logger.debug(f"{aline}")
            ret = f"{ret}{aline}\n"
        return ret

    @classmethod
    def logger(cls, component, level: str = None):
        if component is None:
            raise LogException("component must be a CsvPaths or CsvPath instance")
        #
        # component name
        #
        name = None
        c = f"{component.__class__}"
        if c.find("CsvPaths") > -1:
            name = "csvpaths"
        elif c.find("CsvPath") > -1:
            name = "csvpath"
        else:
            raise LogException("component must be a CsvPaths or CsvPath instance")
        #
        # level
        #
        if level is None:
            level = (
                component.config.csvpaths_log_level
                if name == "csvpaths"
                else component.config.csvpath_log_level
            )
        if level == "error":
            level = logging.ERROR  # pragma: no cover
        elif level == "warn":
            level = logging.WARNING  # pragma: no cover
        elif level == "debug":
            level = logging.DEBUG
        elif level == "info":
            level = logging.INFO
        else:
            raise LogException(f"Unknown log level '{level}'")
        #
        # instance
        #
        logger = None
        if name in LogUtility.LOGGERS:
            logger = LogUtility.LOGGERS[name]
        else:
            log_file_handler = RotatingFileHandler(
                filename=component.config.log_file,
                maxBytes=component.config.log_file_size,
                backupCount=component.config.log_files_to_keep,
            )
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            )
            log_file_handler.setFormatter(formatter)
            logger = None
            logger = logging.getLogger(name)
            logger.addHandler(log_file_handler)
            LogUtility.LOGGERS[name] = logger
        logger.setLevel(level)
        return logger
