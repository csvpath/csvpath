from typing import NewType
import traceback

from csvpath.managers.metadata import Metadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.util.references.reference_parser import ReferenceParser
from csvpath.util.config import Config
from csvpath.util.nos import Nos

from .protocol_utility import ProtocolUtility


ConfigPath = NewType("ConfigPath", str)
FilePath = NewType("FilePath", str)
Namespace = NewType("Namespace", str)


class NameUtility:
    @classmethod
    def namespace_and_name_2(
        cls,
        *,
        config: Config,
        mdata: Metadata,
        entity: str = None,
        job_type: str = None,
        eom: str = None,
        instance: str = None,
        instance_file: str = None,
        root: str = None,
    ) -> tuple[Namespace, FilePath]:
        if root is None:
            root = cls._root(config=config, mdata=mdata)
        ns = ProtocolUtility.update_protocol_if_2(config=config, mdata=mdata, root=root)
        name = cls.build_name(
            config=config,
            job_type=job_type,
            entity=entity,
            eom=eom,
            instance=instance,
            instance_file=instance_file,
        )
        # print(f"naut: ns: {ns}, name: {name}")
        return ns, name

    @classmethod
    def build_name(
        cls,
        *,
        config: Config,
        job_type: str,
        entity: str,
        eom: str = "entity",
        instance: str = None,
        instance_file: str = None,
    ) -> str:
        #
        # job_type is the type of event:
        #   - register
        #   - load
        #   - run
        #
        # eom is the type of name we want:
        #   - `entity` a name for a named-entity action. this indicates using a verb
        #   - `output` the name of an output that becomes the named-entity
        #   - `manifest` indicates we are naming a manifest.json file output
        #
        # we build names using:
        #  - named-entity name
        #  - verb, if a job
        #  - sep, a path segment separator; default is `.`
        #  - instance, the identity of the current csvpath, if we're in a run
        #
        if eom not in ["e", "o", "m", "entity", "output", "manifest"]:
            raise ValueError(f"Unknown build goal: {eom}")

        key = "job_"
        key = f"{key}{job_type}"

        pattern = config.get(section="openlineage", name=f"{key}_{eom}")
        if pattern is None:
            raise ValueError(f"No pattern for {key}_{eom}")

        t = {}
        s = config.get(section="openlineage", name="path_separator")
        if s is None:
            s = "."
        t["sep"] = s
        if pattern.find("verb"):
            v = config.get(section="openlineage", name=f"{key}_verb")
            if v is None:
                raise ValueError(f"No verb for {key}_verb")
            t["verb"] = v
        t["entity"] = entity
        if instance:
            t["instance"] = instance
        if instance_file:
            t["file"] = instance_file
        return pattern.format(**t)

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
        if path is None:
            raise ValueError("Path cannot be None")
        if namespace is None:
            raise ValueError("Namespace cannot be None")

        if path.startswith(namespace):
            path = path[len(namespace) + 1 :]
            return path
        elif path.find(namespace) > -1:
            home = path[path.find(namespace) + len(namespace) + 1 :]
            return home
        return path

    @classmethod
    def _name(cls, *, config: Config, name: str, name_type: str, prefix: None) -> str:
        if name_type is None:
            raise ValueError("Name_type cannot be None")
        sep = config.get(section="openlineage", name="name_separator", default="")
        if prefix is None:
            prefix = config.get(section="openlineage", name="name_prefix", default="")
        nameonly = config.get(
            section="openlineage", name="name_path", default="name-only"
        )
        if nameonly == "name-only":
            base = None
            if name_type in ["csvpaths", "files"]:
                base = config.get(section="inputs", name=name_type)
            else:
                base = config.get(section="results", name="archive")
            sep = Nos(base).sep
            i = name.find(base)
            if i > -1:
                name = name[i + 1 :]
            i = name.find(sep)
            if i > -1:
                name = name[0:sep]
        name = f"{prefix}{sep}{name}"
        return name

    #
    # gets a namespace and path that may not match the metadata
    # passed in. e.g. a run input will be a named-file or named-path
    # but the metadata will be ResultsMetadata
    #
    # manifests also have to use this method, even though they
    # match with the metadata.
    #
    # - only ResultMetadata needs parent
    # - name_string will be looked up by matching root, if not passed
    # - only config and metadata are manditory, other fields if None get the defaults
    @classmethod
    def namespace_and_name(
        cls,
        *,
        config: Config,
        mdata: Metadata,
        name: str = None,
        path: str = None,
        parent: str = None,
        root: ConfigPath = None,
        name_string: str = None,
        tsep: str = None,
    ) -> tuple[Namespace, FilePath]:
        if root is None:
            root = cls._root(config=config, mdata=mdata)
        ns = ProtocolUtility.update_protocol_if_2(config=config, mdata=mdata, root=root)
        if name_string is None:
            name_string = cls._name_string(config=config, mdata=mdata, root=root)
        if name is None:
            name = cls._name(config=config, mdata=mdata)
        if path is None:
            path = cls._path(config=config, mdata=mdata)
        if parent is None:
            parent = cls._parent(config=config, mdata=mdata)
        if tsep is None:
            tsep = config.get(section="openlineage", name="path_separator")

        name = cls.create_specific_name(
            name=name,
            path=path,
            root=root,
            name_string=name_string,
            parent=parent,
            tsep=tsep,
        )
        """
        if isinstance(mdata, FileMetadata):
            print(f"\nx_namespace_and_name: mdata: {type(mdata)}")
            print(f"nspn: ns: {ns}")
            print(f"nspn: name: {name}")
            print(f"nspn: path: {path}")
            print(f"nspn: parent: {parent}")
            print(f"nspn: root: {root}")
            print(f"nspn: name_string: {name_string}")
            print(f"nspn: tsep: {tsep}")
            print(f"found: ns: {ns}, name: {name}")
        """
        return ns, name

    @classmethod
    def _name_string(cls, *, config: Config, mdata: Metadata, root: str = None) -> str:
        if root is None:
            root = cls._root(config=config, mdata=mdata)
        if root == config.get(section="inputs", name="files"):
            return config.get(section="openlineage", name="file_names")
        elif root == config.get(section="inputs", name="csvpaths"):
            return config.get(section="openlineage", name="paths_names")
        parent = cls._parent(config=config, mdata=mdata)
        if parent is None:
            return config.get(section="openlineage", name="results_names")
        else:
            return config.get(section="openlineage", name="result_names")

    @classmethod
    def _root(cls, *, config: Config, mdata: Metadata) -> str:
        root = None
        if isinstance(mdata, FileMetadata):
            root = config.get(section="inputs", name="files")
        elif isinstance(mdata, PathsMetadata):
            root = config.get(section="inputs", name="csvpaths")
        elif isinstance(mdata, ResultMetadata):
            root = config.get(section="results", name="archive")
        elif isinstance(mdata, ResultsMetadata):
            root = config.get(section="results", name="archive")
        else:
            raise ValueError(f"Mdata can not be {mdata}")
        return root

    @classmethod
    def _name(cls, *, config: Config, mdata: Metadata) -> str:
        name = None
        if isinstance(mdata, FileMetadata):
            name = cls.from_root_major_if(mdata.named_file_name)
        elif isinstance(mdata, PathsMetadata):
            name = cls.from_root_major_if(mdata.named_paths_name)
        elif isinstance(mdata, ResultMetadata):
            name = mdata.instance_home
        elif isinstance(mdata, ResultsMetadata):
            name = mdata.named_results_name
        else:
            raise ValueError(f"Mdata can not be {mdata}")
        return name

    @classmethod
    def _parent(cls, *, config: Config, mdata: Metadata) -> str:
        if isinstance(mdata, ResultMetadata):
            return mdata.named_results_name
        return None

    @classmethod
    def _path(cls, *, config: Config, mdata: Metadata) -> str:
        path = None
        if isinstance(mdata, FileMetadata):
            path = mdata.file_home
        elif isinstance(mdata, PathsMetadata):
            path = mdata.group_file_path
        elif isinstance(mdata, ResultMetadata):
            path = mdata.instance_home
        elif isinstance(mdata, ResultsMetadata):
            path = mdata.run_home
        else:
            raise ValueError(f"Mdata can not be {mdata}")
        return path

    @classmethod
    def create_specific_name(
        cls,
        *,
        name: str,
        path: str,
        root: str,
        name_string: str,
        parent: str = None,
        tsep: str = None,
    ) -> str:
        if name_string is None or str(name_string).strip() == "":
            name_string = "{name}"
        tokens = {}
        relative_path = None
        inner_path = None
        #
        # find relative and inner
        #
        relative_path = cls.trim_namespace_if(namespace=root, path=path)
        inner_path = relative_path
        if parent is None and relative_path.startswith(name):
            inner_path = relative_path[len(name) + 1 :]
        elif parent:
            inner_path = relative_path[len(parent) + 1 :]

        #
        # convert seps
        #
        if str(tsep).strip() not in ["None", ""]:
            sep = Nos(path).sep
            path = path.replace(sep, tsep)
            relative_path = relative_path.replace(sep, tsep)
            inner_path = inner_path.replace(sep, tsep)
        #
        # create the name
        #
        tokens["name"] = name
        if parent:
            tokens["parent"] = parent
        tokens["path"] = path
        tokens["relative_path"] = relative_path
        tokens["inner_path"] = inner_path
        try:
            ret = name_string.format(**tokens)
            return ret
        except KeyError:
            print(traceback.format_exc())
            raise
