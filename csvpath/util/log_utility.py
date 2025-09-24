import traceback
from logging.handlers import RotatingFileHandler
import logging
import threading
import gc
import sys


class LogException(Exception):
    pass


class LogUtility:
    LOGGERS = {}

    @classmethod
    def log_brief_trace(cls, *, logger=None, printer=None, depth=30) -> str:
        trace = "".join(traceback.format_stack())
        lines = trace.split("\n")
        if depth in [-1, 0, "all"]:
            depth = len(lines)
        i = depth if depth <= len(lines) else len(lines)
        ret = f"Brief trace in thread: {threading.current_thread()}"

        if logger:
            logger.debug(ret)
        elif printer:
            printer.print(ret)
        else:
            print(ret)

        while i > 0:
            i = i - 1
            aline = lines[len(lines) - i - 1]
            aline = aline.strip()
            if aline[0:4] != "File":
                continue
            if logger:
                logger.debug(f"{aline}")
            elif printer:
                printer.print(f"{aline}")
            else:
                print(f"{aline}")
            ret = f"{ret}{aline}\n"
        return ret

    @classmethod
    def log_refs(cls, obj, *, logger=None, printer=None) -> str:
        refs = sys.getrefcount(obj)
        s = f"Reference count for {obj}: {refs}"
        if logger:
            logger.debug(s)
        elif printer:
            printer.print(s)
        else:
            print(s)
        referrers = gc.get_referrers(obj)
        s = f"Listing {len(referrers)} referrers:"
        if logger:
            logger.debug(s)
        elif printer:
            printer.print(s)
        else:
            print(s)
        for ref in referrers:
            s = f"  {type(ref)}: {ref}"
            if logger:
                logger.debug(s)
            elif printer:
                printer.print(s)
            else:
                print(s)

    #
    # component must be either a CsvPath or CsvPaths
    #
    @classmethod
    def logger(cls, component, level: str = None):
        #
        # TODO: allow a config obj to be passed in with an indicator of csvpaths or csvpath log
        # so that we can pass in other components w/o having one of those two instances.
        #
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
        config = component.config
        level = (
            level
            if level
            else (
                config.csvpaths_log_level
                if name == "csvpaths"
                else config.csvpath_log_level
            )
        )
        return cls.config_logger(config=config, name=name, level=level)

    @classmethod
    def config_logger(cls, *, config, name: str = None, level: str = None):
        if config is None:
            raise ValueError("Config cannot be None")
        if name is None:
            name = "config"
        if level is None:
            level = "info"
        if level == "error":
            level = logging.ERROR  # pragma: no cover
        elif level in ["warn", "warning"]:
            level = logging.WARNING  # pragma: no cover
        elif level == "debug":
            level = logging.DEBUG
        elif level == "info":
            level = logging.INFO
        else:
            raise LogException(f"Unknown log level '{level}'")
        logger = None
        if name in LogUtility.LOGGERS:
            logger = LogUtility.LOGGERS[name]
        else:
            log_file_handler = None
            handler_type = config.get(section="logging", name="handler", default="file")
            log_file_handler = None
            if handler_type == "file":
                log_file_handler = logging.FileHandler(
                    filename=config.log_file,
                    encoding="utf-8",
                )
            elif handler_type == "rotating":
                log_file_handler = RotatingFileHandler(
                    filename=config.log_file,
                    maxBytes=config.log_file_size,
                    backupCount=config.log_files_to_keep,
                    encoding="utf-8",
                )
            else:
                raise ValueError(f"Unknown type of log file handler: {handler_type}")
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

    """
    @classmethod
    def logger(cls, component, level: str = None):
        #
        # TODO: allow a config obj to be passed in with an indicator of csvpaths or csvpath log
        # so that we can pass in other components w/o having one of those two instances.
        #
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
        elif level in ["warn", "warning"]:
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
            log_file_handler = None
            handler_type = component.config.get(
                section="logging", name="handler", default="file"
            )
            log_file_handler = None
            if handler_type == "file":
                log_file_handler = logging.FileHandler(
                    filename=component.config.log_file,
                    encoding="utf-8",
                )
            elif handler_type == "rotating":
                log_file_handler = RotatingFileHandler(
                    filename=component.config.log_file,
                    maxBytes=component.config.log_file_size,
                    backupCount=component.config.log_files_to_keep,
                    encoding="utf-8",
                )
            else:
                raise ValueError(f"Unknown type of log file handler: {handler_type}")
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
    """
