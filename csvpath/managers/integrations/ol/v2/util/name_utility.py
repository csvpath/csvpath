from typing import NewType

from csvpath.managers.metadata import Metadata
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.config import Config
from .protocol_utility import ProtocolUtility


ConfigPath = NewType("ConfigPath", str)
FilePath = NewType("FilePath", str)
Namespace = NewType("Namespace", str)


class NameUtility:
    @classmethod
    def from_root_major_if(cls, name: str) -> str:
        if name is None:
            return None
        name = name.strip()
        if name[0] == "$":
            name = ReferenceParser(name).root_major
        return name

    @classmethod
    def trim_namespace_if(cls, *, namespace: str, path: str) -> str:
        if path.startswith(namespace):
            path = path[len(namespace) + 1 :]
            return path
        elif path.find(namespace) > -1:
            home = path[path.find(namespace) + len(namespace) + 1 :]
            return home
        return path

    #
    # this method:
    #  1. converts reference to root_major, if needed
    #  2. trims the namespace out of the name path
    #  3. revises the namespace according to the openlineage.namespace config setting
    #
    @classmethod
    def namespace_and_name(
        cls, *, config: Config, mdata: Metadata, namespace: ConfigPath, path: FilePath
    ) -> tuple[Namespace, FilePath]:
        path = cls.from_root_major_if(path)
        path = cls.trim_namespace_if(namespace=namespace, path=path)
        ns = ProtocolUtility.update_protocol_if(
            config=config, mdata=mdata, root=namespace
        )
        return ns, path
