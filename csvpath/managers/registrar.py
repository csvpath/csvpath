from abc import ABC
from .metadata import Metadata
from csvpath.util.exceptions import InputException
from .listener import Listener
from ..util.class_loader import ClassLoader


class Registrar(ABC):
    def __init__(self, csvpaths) -> None:
        self.csvpaths = csvpaths
        self.listeners: list[Listener] = [self]

    def register_start(self, mdata: Metadata) -> None:
        self.distribute_update(mdata)

    def register_complete(self, mdata: Metadata) -> None:
        self.distribute_update(mdata)

    def distribute_update(self, mdata: Metadata) -> None:
        """any Listener will recieve a copy of a metadata that describes a
        change to a named-file, named-paths, or named-results."""
        if mdata is None:
            raise InputException("Metadata cannot be None")
        if self.listeners[0] is not self:
            raise InputException("Registrar must be the first metadata listener")
        for lst in self.listeners:
            lst.metadata_update(mdata)

    def add_listener(self, listener: Listener) -> None:
        """adds a listener that will recieve Metadata on changes known to this
        Registrar. the registrar itself is expected to be the first listener
        with the goal that it does its manifest writes in the same way that
        another system would update from the metadata and that the manifest
        writes are done before other systems' listeners receive the metadata,
        in case they have a use for the manifest."""
        self.listeners.append(listener)

    def load_additional_listeners(self, listener_type_name: str) -> None:
        """look in [listeners] for listener_type_name keyed lists of listener classes"""
        ss = self.csvpaths.config.additional_listeners(listener_type_name)
        if ss and not isinstance(ss, list):
            ss = [ss]
        if ss and len(ss) > 0:
            for lst in ss:
                self.load_additional_listener(lst)

    def load_additional_listener(self, load_cmd: str) -> None:
        loader = ClassLoader()
        alistener = loader.load(load_cmd)
        if alistener is not None:
            alistener.config = self.csvpaths.config
            self.add_listener(alistener)

    def remove_listeners(self) -> None:
        """it is not possible to remove the registrar as listener"""
        self.listeners = [self]

    def remove_listener(self, listener: Listener) -> None:
        if listener != self and listener in self.listeners:
            self.listeners.remove(listener)
