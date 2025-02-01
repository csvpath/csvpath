from abc import ABC
from csvpath.util.exceptions import InputException
from .metadata import Metadata
from .listener import Listener
from .errors.error import Error
from ..util.class_loader import ClassLoader


class Registrar(ABC):
    def __init__(self, csvpaths, result=None) -> None:
        if csvpaths:
            self.csvpaths = csvpaths
        self.result = result
        self._type_name = None
        self._internal_listeners = []

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

    def add_internal_listener(self, lst: Listener) -> None:
        if hasattr(lst, "csvpaths"):
            setattr(lst, "csvpaths", self.csvpaths)
        if hasattr(lst, "result"):
            setattr(lst, "result", self.result)
        if not lst.config:
            lst.config = self.csvpaths.config
        self._internal_listeners.append(lst)

    def distribute_update(self, mdata: Metadata) -> None:
        """any Listener will recieve a copy of a metadata that describes a
        change to a named-file, named-paths, named-results, etc."""
        if mdata is None:
            raise InputException("Metadata cannot be None")
        listeners = [self] + self._internal_listeners
        #
        # if we don't have a csvpath we're working with a one-off CsvPath instance.
        # we don't allow integrations to act on CsvPath events. and with the
        # notable exception of errors, errors are not thrown in non-CsvPaths code.
        #
        if self.csvpaths is not None:
            self.load_additional_listeners(self.type_name, listeners)
        for lst in listeners:
            lst.metadata_update(mdata)

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
            if ss and not isinstance(ss, list):
                ss = [ss]
            if ss and len(ss) > 0:
                for lst in ss:
                    self.load_additional_listener(lst, listeners)

    def load_additional_listener(self, load_cmd: str, listeners: list) -> None:
        loader = ClassLoader()
        alistener = loader.load(load_cmd)
        if alistener is not None:
            if hasattr(alistener, "csvpaths"):
                setattr(alistener, "csvpaths", self.csvpaths)
            if hasattr(alistener, "result"):
                setattr(alistener, "result", self.result)
            if hasattr(self, "csvpath") and hasattr(alistener, "csvpath"):
                alistener.csvpath = self.csvpath
            alistener.config = self.csvpaths.config
            listeners.append(alistener)
