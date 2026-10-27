import traceback
from abc import ABC
from csvpath.util.exceptions import InputException, RequiredListenerException
from .metadata import Metadata
from .listener import Listener
from ..util.class_loader import ClassLoader


class Registrar(ABC):
    #
    # the root ledger status of a registration or load that succeeded, or
    # failed. every ledger entry has a status; none is implied by absence.
    # COMPLETE is the same string as ResultsRegistrar.COMPLETE, so
    # :status("complete") means the same thing for every datatype.
    #
    COMPLETE = "complete"
    FAILED = "failed"

    def __init__(self, csvpaths, result=None) -> None:
        #
        # what was the thinking here? should we make this an
        # always present noneable field?
        #
        if csvpaths:
            self.csvpaths = csvpaths
        self.result = result
        self._type_name = None
        #
        # built-in listeners always run, right after the registrar itself and
        # before any other listener, whatever [listeners] groups says. e.g.
        # the named-files and named-paths root ledger writers.
        #
        self._built_in_listeners = []
        self._internal_listeners = []
        self._skips_logged = set()

    @property
    def type_name(self) -> str:
        return self._type_name

    @type_name.setter
    def type_name(self, t: str) -> None:
        self._type_name = t

    def register_start(self, mdata: Metadata) -> None:
        self.distribute_update(mdata)

    def register_complete(self, mdata: Metadata) -> None:
        self.distribute_update(mdata)

    def add_built_in_listener(self, lst: Listener) -> None:
        if lst is None:
            raise ValueError("Listener cannot be None")
        self._attach(lst)
        self._built_in_listeners.append(lst)

    def add_internal_listener(self, lst: Listener) -> None:
        self._attach(lst)
        self._internal_listeners.append(lst)

    def _attach(self, lst: Listener) -> None:
        if hasattr(lst, "csvpaths"):
            setattr(lst, "csvpaths", self.csvpaths)
        if hasattr(lst, "result"):
            setattr(lst, "result", self.result)
        if not lst.config:
            lst.config = self.csvpaths.config

    def distribute_update(self, mdata: Metadata) -> None:
        """any Listener will recieve a copy of a metadata that describes a
        change to a named-file, named-paths, named-results, etc."""

        if mdata is None:
            raise InputException("Metadata cannot be None")
        listeners = [self] + self._built_in_listeners + self._internal_listeners
        #
        # if we don't have a csvpath we're working with a one-off CsvPath instance.
        # we don't allow integrations to act on CsvPath events. and with the
        # notable exception of errors, errors are not thrown in non-CsvPaths code.
        #
        if self.csvpaths is not None:
            self.csvpaths.logger.info("Distributing updates to listeners")
            try:
                self.load_additional_listeners(self.type_name, listeners)
            except Exception as ex:
                print(traceback.format_exc())
                if self.csvpaths:
                    self.csvpaths.logger.error(f"Error in loading listeners: {ex}")
        for lst in listeners:
            if self.csvpaths:
                self.csvpaths.logger.debug(
                    "Updating listener %s with metadata %s", lst, mdata
                )
                #
                # this is important. is this the best place to do it?
                #
                lst.csvpaths = self.csvpaths
            else:
                if self.result and self.result.csvpath:
                    self.result.csvpath.logger.warn("No csvpaths on Registrar")
                else:
                    #
                    # no result and no csvpath likely just means we are in a
                    # CsvPath only context.
                    #
                    ...
            try:
                lst.metadata_update(mdata)
            except Exception as ex:
                self._listener_failed(lst=lst, ex=ex)

    def distribute_patch(self, mdata: Metadata) -> None:
        """a patch to an existing manifest entry. the registrar itself goes
        first and applies the patch, setting mdata.manifest_entry to the
        patched entry. then each listener with a metadata_patch method can
        update its copy. unlike a registration, the registrar's own failure
        always raises and stops the other listeners: a patch is a direct
        request, and a failed one has nothing for them to mirror."""
        if mdata is None:
            raise InputException("Metadata cannot be None")
        for lst, patch in self._listeners_with(method="metadata_patch"):
            try:
                patch(mdata)
            except Exception as ex:
                if lst is self:
                    if self.csvpaths:
                        self.csvpaths.logger.error(f"Patch failed: {ex}")
                    raise
                self._listener_failed(lst=lst, ex=ex)

    def distribute_failure(self, mdata: Metadata) -> None:
        """a failed registration. each listener with a metadata_failure
        method can record it; the default is to ignore it. the registrar's
        own is the default, so the per-entity manifest is not touched.
        listener failures follow the same policy as updates."""
        if mdata is None:
            raise InputException("Metadata cannot be None")
        for lst, failure in self._listeners_with(method="metadata_failure"):
            try:
                failure(mdata)
            except Exception as ex:
                self._listener_failed(lst=lst, ex=ex)

    def _listeners_with(self, *, method: str) -> list[tuple]:
        """(listener, bound method) for every listener, in distribution
        order, that has the method"""
        if method is None or not isinstance(method, str) or method.strip() == "":
            raise ValueError("Method must be a non-empty str")
        listeners = [self] + self._built_in_listeners + self._internal_listeners
        if self.csvpaths is not None:
            self.csvpaths.logger.info("Distributing %s to listeners", method)
            try:
                self.load_additional_listeners(self.type_name, listeners)
            except Exception as ex:
                print(traceback.format_exc())
                self.csvpaths.logger.error(f"Error in loading listeners: {ex}")
        found = []
        for lst in listeners:
            #
            # getattr because listeners are not required to subclass Listener
            #
            m = getattr(lst, method, None)
            if m is None:
                continue
            if self.csvpaths:
                lst.csvpaths = self.csvpaths
            found.append((lst, m))
        return found

    def _listener_failed(self, *, lst, ex: Exception) -> None:
        print(traceback.format_exc())
        if self.csvpaths:
            self.csvpaths.logger.error(f"Error in distributing an update: {ex}")
        #
        # failures are logged, not raised, unless the listener asks for
        # them to stop the flow. a required update (e.g. the SQL
        # listeners when references rely on SQL) raises a type that
        # do_i_raise(ex) always raises, so the error policy cannot
        # absorb it. getattr because listeners are not required to
        # subclass Listener.
        #
        req = getattr(lst, "update_is_required", None)
        if req is not None and req() is True:
            raise RequiredListenerException(
                f"Required listener {type(lst).__name__} failed: {ex}"
            ) from ex
        rou = getattr(lst, "raise_on_update_error", None)
        if rou is not None and rou() is True:
            raise ex

    def load_additional_listeners(
        self, listener_type_name: str, listeners: list
    ) -> None:
        """if we have a csvpaths we look in config.ini [listeners] for
        listener type-keyed lists of listener classes. only csvpaths
        deals with integrations. if running solo CsvPath doesn't
        involve them.
        """
        if self.csvpaths:
            ss = self.csvpaths.config.additional_listeners(listener_type_name)
            self.csvpaths.logger.info("Loading additional listener type(s) %s", ss)
            if ss and not isinstance(ss, list):
                ss = [ss]
            if ss and len(ss) > 0:
                for lst in ss:
                    self.load_additional_listener(lst, listeners)

    def _is_built_in(self, lst) -> bool:
        return any(type(lst) is type(b) for b in self._built_in_listeners)

    def load_additional_listener(self, load_cmd: str, listeners: list) -> None:
        self.csvpaths.logger.info("Loading additional listener %s", load_cmd)
        try:
            loader = ClassLoader()
            kwargs = {}
            if self.csvpaths:
                kwargs = {"config": self.csvpaths.config}
            alistener = loader.load(load_cmd, [], kwargs)
            if alistener is not None and self._is_built_in(alistener):
                #
                # e.g. an older config's default.file line. the built-in
                # already ran; running it again would write twice. a
                # subclass is a different class, so it still runs.
                #
                name = type(alistener).__name__
                if name not in self._skips_logged:
                    self._skips_logged.add(name)
                    self.csvpaths.logger.info(
                        "Skipping configured listener %s: it is built in", name
                    )
                return
            if alistener is not None:
                if hasattr(alistener, "csvpaths"):
                    setattr(alistener, "csvpaths", self.csvpaths)
                if hasattr(alistener, "result"):
                    setattr(alistener, "result", self.result)
                if hasattr(self, "csvpath") and hasattr(alistener, "csvpath"):
                    alistener.csvpath = self.csvpath
                #
                # for ol v2, we need to use the config init param all listeners
                # have. this is no longer needed. the switch is better for the
                # long run because ol v2 won't be the last listener that needs
                # to make immediate decisions based on config
                #
                # alistener.config = self.csvpaths.config
                #
                listeners.append(alistener)
        except Exception as e:
            print(traceback.format_exc())
            self.csvpaths.logger.error(e)
