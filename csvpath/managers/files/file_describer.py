import json
from typing import NewType

from csvpath.util.nos import Nos
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.references.reference_parser import ReferenceParser

NamedFileName = NewType("NamedFileName", str)


class NamedFileDescriber:

    README = "README.md"
    DEFAULT_README = "# Named-File Documentation\n\n"
    JSON_FILE = "definition.json"
    ON_ARRIVAL = "on_arrival"
    NAMED_PATHS_GROUP = "named_paths_group"
    RUN_METHOD = "run_method"
    TEMPLATE = "template"

    def __init__(self, file_manager) -> None:
        self.file_manager = file_manager

    def _name_for_name(self, name: NamedFileName) -> str:
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.file_manager.csvpaths)
            return ref.root_major
        return name

    # ========== JSON ============

    def store_json(self, name: NamedFileName, j: dict) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.file_manager.named_file_home(name)
        nos = Nos(home)
        if not nos.dir_exists():
            nos.makedirs()
        p = Nos(home).join(self.JSON_FILE)
        with DataFileWriter(path=p) as writer:
            json.dump(j, writer.sink, indent=2)

    def get_json(self, name: NamedFileName) -> dict:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.file_manager.named_file_home(name)
        path = Nos(home).join(self.JSON_FILE)
        nos = Nos(path)
        if nos.exists() is False:
            self.store_json(name, {})
        with DataFileReader(path) as file:
            return json.load(file.source)

    # ========== Templates ============

    def get_template(self, name: NamedFileName) -> str:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        config = self.get_json(name)
        if config is None:
            raise ValueError(f"No config for {name}")
        return config.get(self.TEMPLATE)

    def store_template(self, name: NamedFileName, template: str) -> None:
        name = self._name_for_name(name)
        config = self.get_json(name)
        if config is None:
            raise ValueError(f"No config for {name}")
        config[self.TEMPLATE] = template
        self.store_json(name, config)

    # ========== MD file ============

    def store_readme(self, name: NamedFileName, readme: str) -> None:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.file_manager.named_file_home(name)
        p = Nos(home).join(self.README)
        with DataFileWriter(path=p) as writer:
            writer.write(readme)

    def get_readme(self, name: NamedFileName) -> dict:
        if name is None:
            raise ValueError("Name cannot be None")
        name = self._name_for_name(name)
        home = self.file_manager.named_file_home(name)
        path = Nos(home).join(self.README)
        nos = Nos(path)
        if nos.exists() is False:
            self.store_readme(name, self.DEFAULT_README)
        with DataFileReader(path) as file:
            return file.read()

    # ========== on arrival ============

    def get_on_arrival(self, name: NamedFileName) -> dict:
        j = self.get_json(name)
        on = j.get(self.ON_ARRIVAL)
        if on is None:
            on = {}
            j["on_arrival"] = on
            self.store_json(name, j)
        return on

    def store_on_arrival(self, name: NamedFileName, on: dict) -> None:
        j = self.get_json(name)
        if on is None:
            del j[self.ON_ARRIVAL]
        else:
            j[self.ON_ARRIVAL] = on
        self.store_json(name, j)
