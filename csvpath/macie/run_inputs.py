import hashlib
import json
import logging

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from .macie_exceptions import MacieException
from .macie_wrapper_loader import MacieWrapperLoader
from .project_rulesbase import ProjectRulesbase


class RunInputs:
    """copies a named-paths group's Macie inputs into a run's _extra_data,
    so the run can be replicated with the exact rules it used
    (specs/macie/rulesbase-design.md, P2b). _extra_data is the Framework's
    place for non-standard inputs, background and side-effects:

        <run dir>/_extra_data/macie/
          <wrapper>.macie.json              each wrapper in the group home
          <wrapper>.macie.json.report.json  and its conversion report
          macie_catalog.json                the catalog snapshot
          lists/<list id>.txt               each text allow list
          inputs.json                       the group, and each file's sha256

    The first Macie csvpath of a run copies; a later one in the same run
    finds inputs.json and checks the group's files still hash the same,
    failing loudly if one changed mid-run. Paths go through Nos and the
    Framework's readers and writers, so any backend works."""

    DIR = "macie"
    LISTS = "lists"
    INDEX = "inputs.json"
    EXTRA = "_extra_data"

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def record(cls, *, csvpath) -> str | None:
        """copies the inputs for a group run and returns the macie
        directory; None, and nothing written, outside a group run"""
        if csvpath is None:
            raise ValueError("csvpath cannot be None")
        group = csvpath.named_paths_name
        run_dir = csvpath.run_dir
        if csvpath.csvpaths is None or group is None or run_dir is None:
            return None
        files = cls.inputs(paths_manager=csvpath.csvpaths.paths_manager, group=group)
        target = Nos(Nos(run_dir).join(cls.EXTRA)).join(cls.DIR)
        index_path = Nos(target).join(cls.INDEX)
        hashes = {name: cls.sha256(text=text) for name, text in files.items()}
        if Nos(index_path).exists():
            cls._check(index_path=index_path, group=group, hashes=hashes)
            return target
        for name, text in files.items():
            cls._write(path=cls._join(base=target, name=name), text=text)
        index = {"group": group, "files": hashes}
        cls._write(path=index_path, text=json.dumps(index, indent=2) + "\n")
        return target

    @classmethod
    def inputs(cls, *, paths_manager, group: str) -> dict[str, str]:
        """the group's Macie inputs as {name in the macie directory: text}"""
        home = paths_manager.named_paths_home(group)
        out = {}
        for f in sorted(Nos(home).listdir(files_only=True)):
            name = f.rsplit("/", 1)[-1]
            if MacieWrapperLoader.is_wrapper_path(path=name) or name.endswith(
                f"{MacieWrapperLoader.SUFFIX}.report.json"
            ):
                out[name] = cls._read(path=Nos(home).join(name))
        am = paths_manager.asset_manager
        catalog = am.get_asset_file(group, ProjectRulesbase.CATALOG_ASSET)
        if catalog is not None:
            out[ProjectRulesbase.CATALOG_ASSET] = catalog
        assets = am.assets_dir_path(group)
        if Nos(assets).dir_exists():
            for f in sorted(Nos(assets).listdir(files_only=True)):
                name = f.rsplit("/", 1)[-1]
                if name.endswith(am.LIST_SUFFIX):
                    out[f"{cls.LISTS}/{name}"] = cls._read(path=Nos(assets).join(name))
        return out

    @classmethod
    def sha256(cls, *, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def _check(cls, *, index_path: str, group: str, hashes: dict) -> None:
        index = json.loads(cls._read(path=index_path))
        if index.get("group") != group or index.get("files") != hashes:
            msg = (
                f"The Macie inputs of named-paths group {group} changed during the "
                f"run: they no longer match {index_path}. Rerun the group"
            )
            cls.logger().error(msg)
            raise MacieException(msg)

    @classmethod
    def _join(cls, *, base: str, name: str) -> str:
        path = base
        for part in name.split("/"):
            path = Nos(path).join(part)
        return path

    @classmethod
    def _read(cls, *, path: str) -> str:
        with DataFileReader(path) as reader:
            return reader.read()

    @classmethod
    def _write(cls, *, path: str, text: str) -> None:
        parent = path.rsplit("/", 1)[0]
        if not Nos(parent).dir_exists():
            Nos(parent).makedirs()
        with DataFileWriter(path=path, mode="w") as writer:
            writer.write(text)
