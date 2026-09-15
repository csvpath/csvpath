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
