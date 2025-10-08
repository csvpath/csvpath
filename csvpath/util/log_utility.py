import traceback
from logging.handlers import RotatingFileHandler
import logging
from logging import Logger
import threading
import gc
import sys
import os


class LogException(Exception):
    pass


class LogUtility:
    #
    # LOGGERS indexes logger names, which are thread-specific, to instance IDs which are
    # globally unique. we need both. to avoid dealing with locks, we need thread specific
    # loggers. to clean up all the thread specific loggers a component may have we need
    # them indexed by instance ID.
    #
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

    @classmethod
    def logger_name(cls, component) -> str:
        if component is None:
            raise ValueError("Component cannot be None")
        #
        #    thread_name.key_or_context name.project_name.obj_id
        #
        # how we use each name component:
        #  - thread: a logging object can be passed between threads. since we want to manage
        #    Manager.loggerDict ourselves w/o locks we need to know there will be no contention
        #  - context: the key holding the project in flightpath: ties the logger to a config.ini
        #  - project: the name of the project: ties logger to a config.ini
        #  - object ID: the id(obj) of the component requesting the logger: gives a specific id
        #    across threads that we can use to index loggers on the same component in different
        #    threads
        #
        iid = id(component)
        cn = component.__class__.__name__
        ctx_name = None
        proj_name = None
        if cn.find("CsvPaths") > -1:
            ctx_name = (
                component.project_context if component.project_context else "csvpaths"
            )
            proj_name = (
                component.project if component.project else "no_project_identified"
            )
        elif cn.find("CsvPath") > -1:
            ctx_name = (
                component.csvpaths.project_context
                if component.csvpaths and component.csvpaths.project_context
                else "no_project_context"
            )
            proj_name = (
                component.csvpaths.project
                if component.csvpaths and component.csvpaths.project
                else "no_projects_available"
            )
        elif cn.find("Config") > -1:
            ctx_name = "config"
            proj_name = cn.rstrip("'>")
            proj_name = cn[cn.rfind(".") :]
        else:
            raise ValueError(
                f"Cannot get a logger name for a {component.__class__.__name__}"
            )
        name = f"{threading.current_thread().name}.{ctx_name}.{proj_name}.{iid}"
        names = cls.LOGGERS.get(iid)
        if names is None:
            names = []
        names.append(name)
        cls.LOGGERS[iid] = names
        return name

    @classmethod
    def release_logger(cls, component) -> None:
        iid = id(component)
        #
        # LOGGERS indexes logger names, which are thread-specific, to instance IDs which are
        # globally unique. we need both. to avoid dealing with locks, we need thread specific
        # loggers. to clean up all the thread specific loggers a component may have we need
        # them indexed by instance ID.
        #
        names = cls.LOGGERS.get(iid)
        if names is None or len(names) == 0:
            return
        for name in names[:]:
            loggerx = logging.getLogger(name)
            for handler in loggerx.handlers[:]:
                try:
                    handler.flush()
                    handler.close()
                    handler.stream = None
                    loggerx.removeHandler(handler)
                except Exception:
                    print(traceback.format_exc())
            #
            # this is the concerning part. we don't have a rock-solid guarantee
            # that the logging system will never change the loggerDict in some way
            # we believe it will not change because it is not '_' private and it
            # is a known/referred-to thing. but there is some risk.
            #
            if name not in Logger.manager.loggerDict:
                print(
                    f"===============\n Lout Error: logger {name} not held by logging\n==============="
                )
            else:
                del Logger.manager.loggerDict[name]
            names.remove(name)
            #
            # the other concerning thing: there was a statement online that log handlers are
            # also held forever in a dict in logging. a quick look suggests only two lists of
            # weak refs, so not a big problem. something to remember, tho.
            #
        del cls.LOGGERS[iid]

    #
    # component must be either a CsvPath or CsvPaths
    #
    @classmethod
    def logger(cls, component, level: str = None):
        if component is None:
            raise LogException("component must be a CsvPaths or CsvPath instance")
        name = None
        name = cls.logger_name(component)
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
    def config_logger(cls, *, config, name: str, level: str = None):
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
        filename = config.log_file
        parentdir = os.path.dirname(filename)
        if not os.path.exists(parentdir):
            os.makedirs(parentdir)
            #
            # this is a bit paranoid
            #
            if not os.path.exists(parentdir):
                raise RuntimeError("Cannot create logging directory: {parentdir}")
        log_file_handler = None
        handler_type = config.get(section="logging", name="handler", default="file")
        log_file_handler = None
        if handler_type == "file":
            log_file_handler = logging.FileHandler(
                filename=filename,
                encoding="utf-8",
            )
        elif handler_type == "rotating":
            log_file_handler = RotatingFileHandler(
                filename=filename,
                maxBytes=config.log_file_size,
                backupCount=config.log_files_to_keep,
                encoding="utf-8",
            )
        else:
            raise ValueError(f"Unknown type of log file handler: {handler_type}")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        log_file_handler.setLevel(level)
        log_file_handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(level)
        #
        # there will be 0, 1, or 2 handlers. we clear them and start fresh.
        #
        for _ in logger.handlers:
            _.flush()
            _.close()
            logger.removeHandler(_)
            _ = None
        logger.addHandler(log_file_handler)
        logger.propagate = False
        return logger
