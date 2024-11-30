from abc import ABC  # , abstractmethod
from .metadata import Metadata
from csvpath.util.exceptions import InputException
from .listener import Listener


class Registrar(ABC):
    def __init__(self) -> None:
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

    def remove_listeners(self) -> None:
        """it is not possible to remove the registrar as listener"""
        self.listeners = [self]

    def remove_listener(self, listener: Listener) -> None:
        if listener != self and listener in self.listeners:
            self.listeners.remove(listener)
