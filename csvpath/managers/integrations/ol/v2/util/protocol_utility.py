from pathlib import Path
from csvpath.managers.metadata import Metadata
from csvpath.util.nos import Nos
from csvpath.util.config import Config
from csvpath.util.azure.azure_utils import AzureUtility as azut
from csvpath.util.references.reference_parser import ReferenceParser

from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata


class ProtocolUtility:
    @classmethod
    def update_protocol_if_2(
        cls, *, config: Config, mdata: Metadata, root: str = None
    ) -> str:
        if config is None:
            raise ValueError("Config cannot be None")
        if mdata is None:
            raise ValueError("Metadata cannot be None")

        root = cls._root(config=config, mdata=mdata, root=root)
        pattern = cls._pattern(config=config, root=root)
        t = cls._gather(config=config, mdata=mdata, root=root)
        return cls._transform(config=config, tokens=t, pattern=pattern)

    @classmethod
    def _gather(cls, config: Config, mdata: Metadata, root: str) -> dict[str, str]:
        prefix = config.get(section="openlineage", name="namespace_prefix", default="")
        root_path = cls._root_path(root)
        sep = config.get(section="openlineage", name="path_separator", default=".")
        root_path_separated = root_path.replace("/", sep).replace("\\", sep)
        protocol_root_path = cls._protocol_root(root)
        root_name = Path(root).name
        entity_name = cls._entity_name(mdata)
        t = {
            "prefix": prefix,
            "root_path": root_path,
            "protocol_root_path": protocol_root_path,
            "root_path_separated": root_path_separated,
            "root_name": root_name,
            "entity_name": entity_name,
        }
        return t

    @classmethod
    def _transform(cls, *, config: Config, pattern: str, tokens: dict[str, str]) -> str:
        try:
            ret = pattern.format(**tokens)
            return ret
        except (KeyError, AttributeError, IndexError, ValueError) as k:
            #
            # log but don't reraise. we'd rather lose or misname an OL
            # event without also losing stability
            #
            config.logger.exception(k)
            return ""

    @classmethod
    def _entity_name(cls, mdata: Metadata) -> str:
        if isinstance(mdata, FileMetadata):
            entity_name = mdata.named_file_name
            entity_name = cls._from_root_major_if(entity_name)
        elif isinstance(mdata, PathsMetadata):
            entity_name = mdata.named_paths_name
            entity_name = cls._from_root_major_if(entity_name)
        else:
            entity_name = mdata.named_results_name
        return entity_name

    @classmethod
    def _pattern(cls, *, config: Config, root: str) -> str:
        pattern = config.get(
            section="openlineage", name="namespace_pattern", default=f"{root}"
        )
        if str(pattern).strip() in ["", "None"]:
            raise ValueError("Namespace pattern cannot be None")
        return pattern

    @classmethod
    def _root_path(cls, root: str) -> str:
        i = root.find("://")
        if i > -1:
            return root[i + 3 :]
        return root

    @classmethod
    def _root(cls, *, config: Config, mdata: Metadata, root: str) -> str:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if config is None:
            raise ValueError("Config cannot be None")
        if root is None or root.strip() == "":
            if isinstance(mdata, FileMetadata):
                root = config.get(section="inputs", name="files")
            elif isinstance(mdata, PathsMetadata):
                root = config.get(section="inputs", name="csvpaths")
            else:
                root = config.get(section="results", name="archive")
        if root is None or root.strip() == "":
            raise ValueError(f"Root path for {type(mdata).__name__} cannot be None")
        return root.strip()

    @classmethod
    def _protocol_root(cls, root: str) -> str:
        nos = Nos(root)
        if nos.is_local:
            if root.startswith("file://"):
                return root
            path = Path(root)
            try:
                ret = path.as_uri()
                return ret
            except ValueError:
                return f"file://{root}"
        elif nos.is_azure:
            p = azut.my_protocol()
            path = root[5:]
            return f"{p}{path}"
        return root

    @classmethod
    def _from_root_major_if(cls, name: str) -> str:
        if name is None:
            return None
        name = name.strip()
        if name == "":
            #
            # would this be a problem to log or raise? or just a naming decision?
            #
            return name
        if name[0] == "$":
            name = ReferenceParser(name).root_major
        return name
