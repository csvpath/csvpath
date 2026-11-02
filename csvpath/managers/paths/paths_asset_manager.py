import re
from typing import NewType


from csvpath.util.nos import Nos
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.references.reference_parser import ReferenceParser

NamedPathsName = NewType("NamedPathsName", str)

#
# TODO: scripts should be handled as assets, not config. move here
# from the describer.
#


class PathsAssetManager:
    ASSETS = "assets"

    def __init__(self, paths_manager) -> None:
        self.paths_manager = paths_manager

    def _name_for_name(self, name: NamedPathsName) -> str:
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.paths_manager.csvpaths)
            return ref.root_major
        return name

    def assets_dir_path(self, name: NamedPathsName) -> str:
        name = self._name_for_name(name)
        if not self.paths_manager.has_named_paths(name):
            raise ValueError(f"No such named-paths group: {name}")
        home = self.paths_manager.named_paths_home(name)
        return Nos(home).join(self.ASSETS)

    def assure_assets_dir(self, name: NamedPathsName) -> None:
        p = self.assets_dir_path
        nos = Nos(p)
        if not nos.direxists():
            Nos(p).makedirs()

    def make_asset_file_path(self, name: NamedPathsName, filename: str) -> str:
        path = self.assets_dir_path(name)
        if not Nos(path).dir_exists():
            Nos(path).makedirs()
        path = Nos(path).join(filename)
        return path

    def store_asset_file(
        self,
        *,
        name: NamedPathsName,
        filename: str,
        contents: str,
        mode: str = "w",
        overwrite: bool = True,
    ) -> None:
        path = self.make_asset_file_path(name, filename)
        if overwrite is False and Nos(path).exists():
            raise ValueError(f"Cannot overwrite {path}")
        with DataFileWriter(path=path, mode=mode) as writer:
            writer.write(contents)

    #
    # lists: value-per-line text files in the assets dir, read by the
    # load_list() function as <list name>.txt
    #
    LIST_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
    LIST_SUFFIX = ".txt"

    @classmethod
    def check_list_name(cls, list_name: str) -> str:
        """a list name is a file name without .txt: letters, digits, '.',
        '_' and '-', starting with a letter or digit"""
        if not isinstance(list_name, str) or cls.LIST_NAME.fullmatch(list_name) is None:
            raise ValueError(
                f"List name {list_name!r} must be letters, digits, '.', '_' or '-', "
                "starting with a letter or digit"
            )
        if list_name.endswith(cls.LIST_SUFFIX):
            raise ValueError(
                f"List name {list_name!r} must not include {cls.LIST_SUFFIX}"
            )
        return list_name

    def list_path(self, *, name: NamedPathsName, list_name: str) -> str:
        """where a group's list is, whether or not it exists. creates
        nothing"""
        self.check_list_name(list_name)
        return Nos(self.assets_dir_path(name)).join(f"{list_name}{self.LIST_SUFFIX}")

    def store_list(
        self, *, name: NamedPathsName, list_name: str, values: list[str]
    ) -> str:
        """writes a list to the group's assets as <list name>.txt, one value
        per line, replacing any list of that name. returns the path."""
        self.check_list_name(list_name)
        if not isinstance(values, list):
            raise TypeError(f"values must be a list, not {type(values)}")
        for v in values:
            if not isinstance(v, str):
                raise TypeError(f"List values must be str, not {type(v)}")
            if "\n" in v or "\r" in v:
                raise ValueError(f"A list value cannot contain a line break: {v!r}")
        path = self.make_asset_file_path(name, f"{list_name}{self.LIST_SUFFIX}")
        with DataFileWriter(path=path, mode="w") as writer:
            writer.write("".join(f"{v}\n" for v in values))
        return path

    def get_asset_file(self, name: NamedPathsName, filename: str) -> None:
        path = self.make_asset_file_path(name, filename)
        if not Nos(path).exists():
            return None
        with DataFileReader(path=path) as reader:
            return reader.read()

    def delete_asset_file(self, name: NamedPathsName, filename: str) -> None:
        path = self.make_asset_file_path(name, filename)
        if Nos(path).exists():
            return Nos(path).remove()

    def list_asset_files(self, name: NamedPathsName) -> None:
        path = self.assets_dir_path(name)
        return Nos(path).listdir(files_only=True)
