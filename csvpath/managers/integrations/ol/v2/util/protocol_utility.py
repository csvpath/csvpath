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
        root = str(root).strip()
        if root in ["", "None"]:
            if isinstance(mdata, FileMetadata):
                root = config.get(section="inputs", name="files")
            elif isinstance(mdata, PathsMetadata):
                root = config.get(section="inputs", name="csvpaths")
            else:
                root = config.get(section="results", name="archive")

        #
        # look in config for [openlineage] namespace
        #   - "" or default: nothing, use bare named-entity path
        #   - project: use bare prefixed by project_context/project, if available
        #   - name: use last path segment of named-entity path
        #   - strip: strip off the protocol, if any
        #
        # to test use config.set(section="listeners", name="openlineage.namespace", value=...)
        #
        pattern = config.get(
            section="openlineage", name="namespace_pattern", default="{root_path}"
        )
        if str(pattern).strip() in ["", "None"]:
            raise ValueError("Namespace pattern cannot be None")

        prefix = config.get(section="openlineage", name="namespace_prefix", default="")
        root_path = root
        i = root.find("://")
        if i > -1:
            root_path = root[i + 3 :]
        sep = config.get(section="openlineage", name="path_separator", default=".")
        root_path_separated = root_path.replace("/", sep).replace("\\", sep)
        protocol_root_path = cls._protocol_root(root)
        root_name = Path(root).name
        entity_name = None
        if isinstance(mdata, FileMetadata):
            entity_name = mdata.named_file_name
            entity_name = cls._from_root_major_if(entity_name)
        elif isinstance(mdata, PathsMetadata):
            entity_name = mdata.named_paths_name
            entity_name = cls._from_root_major_if(entity_name)
        else:
            entity_name = mdata.named_results_name

        t = {
            "prefix": prefix,
            "root_path": root_path,
            "protocol_root_path": protocol_root_path,
            "root_path_separated": root_path_separated,
            "root_name": root_name,
            "entity_name": entity_name,
        }
        ret = pattern.format(**t)
        return ret

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
                # print(traceback.format_exc())
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
        if name[0] == "$":
            name = ReferenceParser(name).root_major
        return name

    #
    # ------------------------------------------
    #

    @classmethod
    def update_protocol_if(cls, *, config: Config, mdata: Metadata, root: str) -> str:
        if root is None:
            raise ValueError("URI cannot be None")
        root = str(root).strip()
        if root == "":
            raise ValueError("URI cannot be empty")
        if config is None:
            raise ValueError("Config cannot be None")
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        #
        # look in config for [openlineage] namespace
        #   - "" or default: nothing, use bare named-entity path
        #   - project: use bare prefixed by project_context/project, if available
        #   - name: use last path segment of named-entity path
        #   - strip: strip off the protocol, if any
        #
        # to test use config.set(section="listeners", name="openlineage.namespace", value=...)
        #
        ns = config.get(section="openlineage", name="namespace", default="default")
        if ns is None:
            ns = ["default"]
        if isinstance(ns, str):
            ns = [ns]
        if len(ns) == 0:
            ns = ["default"]
        ret = cls._strip_if(config=config, root=root, ns=ns)
        ret = cls._name_if(config=config, root=ret, ns=ns)
        ret = cls._project_if(config=config, mdata=mdata, root=ret, ns=ns)
        ret = cls._default_if(config=config, root=ret, ns=ns)
        return ret

    @classmethod
    def _strip_if(cls, *, config: Config, root: str, ns: list[str]) -> str:
        if "strip" not in ns:
            return root
        root = cls._strip_protocol_if(config=config, root=root)
        return root

    @classmethod
    def _name_if(cls, *, config: Config, root: str, ns: list[str]) -> str:
        if "name" not in ns:
            return root
        _ = Path(root).name
        pfix = config.get(section="openlineage", name="namespace_prefix", default="")
        sep = config.get(section="openlineage", name="path_separator", default="")
        if _ == "":
            return f"{pfix}{sep}{root}"
        return f"{pfix}{sep}{_}"

    @classmethod
    def _project_if(
        cls, *, config: Config, mdata: Metadata, root: str, ns: list[str]
    ) -> str:
        if "project" not in ns:
            return root
        _ = ""
        if mdata.project_context is not None:
            _ = mdata.project_context
        if mdata.project is not None:
            _ = f"{_}/{mdata.project}" if _ != "" else mdata.project
        ret = None
        pfix = config.get(section="openlineage", name="namespace_prefix", default="")
        if _ == "":
            ret = f"{pfix}{cls._strip_protocol_if(config=config, root=root)}"
        else:
            ret = f"{pfix}{cls._strip_protocol_if(config=config, root=_)}"
        if _ != "":
            sep = config.get(section="openlineage", name="path_separator", default="")
            last = Path(root).name
            ret = f"{ret}{sep}{last}"
        return ret

    @classmethod
    def _default_if(cls, *, config: Config, root: str, ns: list[str]) -> str:
        if "default" not in ns:
            return root
        nos = Nos(root)
        if nos.is_local:
            if root.startswith("file://"):
                return root
            path = Path(root)
            try:
                return path.as_uri()
            except ValueError:
                return root
        elif nos.is_azure:
            p = azut.my_protocol()
            path = root[5:]
            return f"{p}{path}"
        return root

    @classmethod
    def _strip_protocol_if(cls, *, config: Config, root: list[str]) -> str:
        i = root.find("://")
        if i == -1:
            return root
        return root[i + 3 :]
