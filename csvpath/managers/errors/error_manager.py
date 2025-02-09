import os
from typing import Any
from datetime import datetime, timezone
from csvpath.util.config import OnError
from csvpath.matching.productions import Matchable
from csvpath.matching.util.exceptions import MatchException
from csvpath.modes.error_mode import ErrorMode
from ..registrar import Registrar
from ..listener import Listener
from ..metadata import Metadata
from .error import Error


class ErrorManager(Registrar, Listener):
    """creates errors uses the csvpaths's or csvpath's error policy to handle them."""

    def __init__(self, *, csvpaths=None, csvpath=None, error_collector=None):
        self.csvpath = csvpath
        self._csvpaths = None
        if csvpaths is not None:
            self.csvpaths = csvpaths
        elif csvpath and csvpath.csvpaths is not None:
            self.csvpaths = csvpath.csvpaths
        if self.csvpath is None and self.csvpaths is None:
            raise ValueError("CsvPaths and/or CsvPath must be provided")
        self._collector = csvpath if csvpath else csvpaths
        #
        #
        #
        Registrar.__init__(self, csvpaths=csvpaths)
        Listener.__init__(self, csvpath.config if csvpath else csvpaths.config)
        #
        #
        #
        self.ecoms = None
        if self.csvpath:
            self.ecoms = self.csvpath.ecoms
        elif self.csvpaths:
            self.ecoms = self.csvpaths.ecoms
        else:
            raise Exception("No csvpaths or csvpath available")
        self.type_name = "error"
        self.vetos = {}
        self.error_metrics = None
        self.full_format = None

    @property
    def csvpaths(self):
        return self._csvpaths

    @csvpaths.setter
    def csvpaths(self, paths):
        #
        # added to debug. there shouldn't be a time when we're setting None, but
        # this None test could go away.
        #
        if paths is None:
            raise ValueError("CsvPaths cannot be None")
        self._csvpaths = paths

    #
    # a matchable can request that all handle_error() calls for a list of
    # its children be redirected back to it for handling. this is mainly for
    # or(). or() needs to know all its branches failed before reporting errors.
    # or catches MatchExceptions and vetos handle_errors, instead resending
    # them if needed after checking the branches.
    #
    def veto_callback(self, *, sources: list[Matchable], callback: Matchable) -> None:
        self.vetos[callback] = sources

    #
    # source will most often be a matchable or another CsvPaths manager.
    # main message is the most important info provided by the source.
    # other keyword args TBD. we don't expect exception objects. exceptions
    # are a long jump that is a different signaling channel from errors.
    #
    def handle_error(self, *, source: Any, msg: str, **kwargs) -> None:
        if source is None:
            raise ValueError("Source cannot be None")
        if msg is None:
            raise ValueError("Error message cannot be None")
        #
        # delegate if requested for this source. we'll delegate as
        # many times as requested.
        #
        found = False
        for k, v in self.vetos.items():
            if source in v:
                k.handle_error(source=source, msg=msg)
                found = True
        if found is True:
            return
        error = Error(source=source, msg=msg, error_manager=self)
        if self.csvpath:
            if self.csvpath.line_monitor:
                error.line_count = (
                    self.csvpath.line_monitor.physical_line_number
                    if self.csvpath
                    else -1
                )
            error.match_count = self.csvpath.match_count if self.csvpath else -1
            error.scan_count = self.csvpath.scan_count if self.csvpath else -1
            error.filename = (
                self.csvpath.scanner.filename
                if self.csvpath and self.csvpath.scanner
                else None
            )
            error.match = self.csvpath.match
        error.message = msg
        error.expanded_message = self.decorate_error(source=source, msg=msg)
        self.distribute_update(error)

    def decorate_error(self, *, source, msg: str) -> str:
        #
        # at some point we may want this to be configurable. for now:
        #
        # time:file-name:paths-name:instance-name:source-chain: msg
        #
        t = datetime.now(timezone.utc)
        t = t.strftime("%Y-%m-%d %Hh%Mm%Ss-%f")
        file = ""
        paths = ""
        instance = ""
        chain = ""
        line = (
            self.csvpath.line_monitor.physical_line_number
            if self.csvpath is not None
            else -1
        )
        try:
            if isinstance(source, Matchable):
                file = source.matcher.csvpath.named_file_name
                if file is None:
                    file = source.matcher.csvpath.scanner.filename
                    i = file.rfind(os.sep)
                    if i > -1:
                        file = file[i + 1 :]
                paths = source.matcher.csvpath.named_paths_name
                if paths is None:
                    paths = ""
                instance = source.matcher.csvpath.identity
                if instance is None:
                    instance = ""
                chain = source.my_chain
            if hasattr(source, "named_file_name"):
                file = (
                    source.named_file_name
                    if source.named_file_name is not None
                    else file
                )
            if hasattr(source, "named_paths_name"):
                paths = (
                    source.named_paths_name
                    if source.named_paths_name is not None
                    else paths
                )
            if instance == "" and hasattr(source, "identity"):
                instance = source.identity if source.identity is not None else ""
            if chain is None or chain == "":
                chain = f"{type(source)}".rstrip("'>")
                chain = chain[chain.rfind("'") :]
        except Exception as e:
            #
            #
            #
            self._collector.logger.error(e)
        if self.full_format is None:
            self.full_format = (
                "{time}:{file}:{line}:{paths}:{instance}:{chain}: {message}"
            )
            if self.csvpath is not None:
                f = self.csvpath.config.get(
                    section="errors", name="pattern", default=self.full_format
                )
                if f is not None and f.strip() != "":
                    self.full_format = f
        return self.format(
            time=t,
            file=file,
            paths=paths,
            instance=instance,
            chain=chain,
            line=line,
            message=msg,
        )

    def format(self, *, time, file="", paths="", instance="", chain="", line, message):
        # TODO: a better solution that doesn't use exec
        f = self.full_format
        f = f.replace("{time}", time)
        f = f.replace("{file}", file)
        f = f.replace("{paths}", paths)
        f = f.replace("{instance}", instance)
        f = f.replace("{chain}", chain)
        f = f.replace("{line}", f"{line}")
        f = f.replace("{message}", message)
        return f

    # listeners must include:
    #   - self on behalf of CsvPath
    #   - all Expressions
    #   - Result, if there is a CsvPaths
    #
    # ==========================================
    #
    # we add all Matcher's Expressions (match components) using this method.
    # they listen to maintain their own error count.
    # update: now using add_internal_listener() on Registrar parent
    #
    # self.add_listeners(lst)
    #
    # this method listens onbehalf of the CsvPath. it logs, stops, fails,
    # prints, and collects
    #
    def metadata_update(self, mdata: Metadata) -> None:
        #
        # you cannot turn off logging complete. you can turn off collection in config.ini
        # but not in the csvpath modes. both of these things could change.
        #
        if self.ecoms.do_i_quiet():
            self._collector.logger.error(
                f"Qt {mdata.uuid_string}: message: {mdata.message}"
            )
            self._collector.logger.error(
                f"Qt {mdata.uuid_string}: named_paths_name: {mdata.named_paths_name}"
            )
            self._collector.logger.error(
                f"Qt {mdata.uuid_string}: path identity: {mdata.identity}"
            )
            self._collector.logger.error(
                f"Qt {mdata.uuid_string}: file: {mdata.filename}"
            )
            self._collector.logger.error(
                f"Qt {mdata.uuid_string}: line: {mdata.line_count}"
            )
            self._collector.logger.error(
                f"Qt {mdata.uuid_string}: source: {mdata.source}"
            )
        else:
            self._collector.logger.error(f"{mdata}")
        #
        #
        #
        if self.ecoms.do_i_collect():
            #
            # if we are held by a CsvPath we are the CsvPath's error listener so we're
            # pushing the error back to our parent's public access interface.
            #
            self._collector.collect_error(mdata)
        if self.ecoms.do_i_stop() is True:
            if self.csvpath:
                self.csvpath.stopped = True
        if self.ecoms.do_i_fail() is True:
            if self.csvpath:
                self.csvpath.is_valid = False
        if self.ecoms.do_i_print() is True:
            if self.csvpath:
                msg = mdata.message
                if self.ecoms.do_i_print_expanded():
                    # if self.csvpath.error_mode == ErrorMode.FULL or not self.csvpath:
                    msg = mdata.expanded_message
                self.csvpath.print(f"{msg}")
