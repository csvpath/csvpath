from typing import Any
from csvpath.util.config import OnError
from csvpath.matching.productions import Matchable
from csvpath.matching.util.exceptions import MatchException
from ..registrar import Registrar
from ..listener import Listener
from ..metadata import Metadata
from .error import Error


class ErrorManager(Registrar, Listener):
    """creates errors uses the csvpaths's or csvpath's error policy to handle them."""

    def __init__(self, *, csvpaths=None, csvpath=None, error_collector=None):
        super().__init__(csvpaths=csvpaths)
        self.csvpath = csvpath
        # self.csvpaths = csvpaths
        self._collector = csvpath if csvpath else csvpaths
        self.type = "error"
        self.vetos = {}

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

        # c = self.csvpath.config if self.csvpath else self.csvpaths.config
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
        if isinstance(source, Matchable):
            error.source = source.my_chain
        else:
            error.source = type(source)
        self.distribute_update(error)

    # listeners must include:
    #   - self on behalf of CsvPath
    #   - all Expressions
    #   - Result, if there is a CsvPaths
    #
    # ==========================================

    #
    # we add all Matcher's Expressions (match components) using this method.
    # they listen to maintain their own error count.
    #
    def add_listener(self, lst: Listener) -> None:
        self.internal_listeners.append(lst)

    #
    # this method listens onbehalf of the CsvPath. it logs, stops, fails,
    # prints, and collects
    #
    def metadata_update(self, mdata: Metadata) -> None:
        ecoms = self.csvpath.ecoms if self.csvpath is not None else self.csvpaths.ecoms
        #
        # you cannot turn off logging complete. you can turn off collection in config.ini
        # but not in the csvpath modes. both of these things could change.
        #
        if ecoms.do_i_quiet():
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
        if ecoms.in_policy(OnError.COLLECT.value):
            #
            # if we are held by a CsvPath we are the CsvPath's error listener so we're
            # pushing the error back to our parent's public access interface.
            #
            self._collector.collect_error(mdata)
        if ecoms.do_i_stop() is True:
            if self.csvpath:
                self.csvpath.stopped = True
        if ecoms.do_i_fail() is True:
            if self.csvpath:
                self.csvpath.is_valid = False
        if ecoms.do_i_print() is True:
            if self.csvpath:
                self.csvpath.print(f"{mdata.message}")
