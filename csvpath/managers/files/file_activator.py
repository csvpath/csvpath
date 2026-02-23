import traceback
from typing import NewType
from csvpath.util.references.reference_parser import ReferenceParser

NamedFileName = NewType("NamedFileName", str)


class NamedFileActivator:
    def __init__(self, file_manager) -> None:
        self.file_manager = file_manager

    def _name_for_name(self, name: NamedFileName) -> str:
        if name.startswith("$"):
            ref = ReferenceParser(name, csvpaths=self.csvpaths)
            return ref.root_major
        return name

    def activate_if(self, name: NamedFileName) -> str:
        try:
            if name is None:
                raise ValueError("Name cannot be None")
            describer = self.file_manager.describer
            j = describer.get_json(name)
            if describer.ON_ARRIVAL not in j:
                return
            a = j[describer.ON_ARRIVAL]
            if describer.NAMED_PATHS_GROUP not in a:
                return
            group = a[describer.NAMED_PATHS_GROUP]
            method = a.get(describer.RUN_METHOD)
            if method is None:
                method = "collect_paths"
            if method not in [
                "collect_paths",
                "fast_forward_paths",
                "collect_by_line",
                "fast_forward_by_line",
            ]:
                raise ValueError(
                    f"Unknown run method found in activation descriptor: {method}"
                )
            csvpaths = self.file_manager.csvpaths
            if csvpaths is None:
                raise ValueError("CsvPaths object cannot be None")
            r = getattr(csvpaths, method)
            #
            # r should never be none if we were able to validate the method name already. but doubling the
            # check is essentially free.
            #
            if r is None:
                raise ValueError(
                    f"Unknown run method found in activation descriptor: {method}"
                )
            ref = r(filename=name, pathsname=group)
            return ref
        except Exception:
            print(traceback.format_exc())
            raise
