import unittest


from csvpath.managers.integrations.ol.v2.util.name_utility import NameUtility as naut


class TestCsvPathsExamplesOpenLineageNamesAndProtocols(unittest.TestCase):
    def test_create_name(self) -> None:

        t = {
            "csvpath:{name}": "csvpath:animals",
            "file://{inner_path}": "file://favorites/frogs/green.csv",
            "csvpath://{relative_path}": "csvpath://animals/favorites/frogs/green.csv",
            "{path}": "data/inputs/files/animals/favorites/frogs/green.csv",
            "file:///{path}": "file:///data/inputs/files/animals/favorites/frogs/green.csv",
        }
        #
        # files
        #
        for k, v in t.items():
            name = naut.create_specific_name(
                name="animals",
                path="data/inputs/files/animals/favorites/frogs/green.csv",
                parent=None,
                root="data/inputs/files",
                name_string=k,
                tsep="/",
            )
            print(f"created: {name} from {k}")
            assert name == v
        #
        # result
        #
        t = {
            "csvpath:{name}": "csvpath:sea",
            "file://{inner_path}": "file://unloved/fish/2026-01-01_00-00-00/sea",
            "csvpath://{relative_path}": "csvpath://animals/unloved/fish/2026-01-01_00-00-00/sea",
            "{path}": "data/inputs/paths/animals/unloved/fish/2026-01-01_00-00-00/sea",
            "file:///{path}": "file:///data/inputs/paths/animals/unloved/fish/2026-01-01_00-00-00/sea",
        }
        for k, v in t.items():
            name = naut.create_specific_name(
                name="sea",
                path="data/inputs/paths/animals/unloved/fish/2026-01-01_00-00-00/sea",
                parent="animals",
                root="data/inputs/paths",
                name_string=k,
                tsep="/",
            )
            print(f"created: {name} from {k}")
            assert name == v
