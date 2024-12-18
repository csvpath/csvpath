from abc import ABC
from csvpath.util.exceptions import InputException
from .metadata import Metadata
from .listener import Listener
from ..util.class_loader import ClassLoader


class Registrar(ABC):
    def __init__(self, csvpaths, result=None) -> None:
        self.csvpaths = csvpaths
        self.result = result
        self.type = None

    def register_start(self, mdata: Metadata) -> None:
        self.distribute_update(mdata)

    def register_complete(self, mdata: Metadata) -> None:
        self.distribute_update(mdata)

    def distribute_update(self, mdata: Metadata) -> None:
        """any Listener will recieve a copy of a metadata that describes a
        change to a named-file, named-paths, or named-results."""
        listeners = [self]
        self.load_additional_listeners(self.type, listeners)
        if mdata is None:
            raise InputException("Metadata cannot be None")
        for lst in listeners:
            lst.metadata_update(mdata)

    def load_additional_listeners(
        self, listener_type_name: str, listeners: list
    ) -> None:
        """look in [listeners] for listener_type_name keyed lists of listener classes"""
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
            alistener.config = self.csvpaths.config
            listeners.append(alistener)
