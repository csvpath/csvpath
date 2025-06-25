import unittest
import os
from csvpath import CsvPaths

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
LOOKUP_FILE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}lookup_names.csv"
LOOKUP_PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}metaphone_lookup.csvpaths"


class TestCsvPathsFunctionsMetaphone(unittest.TestCase):
    def test_function_metaphone2(self):
        # load the lookup table
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.add_named_file(name="lookups", path=LOOKUP_FILE)
        paths.paths_manager.add_named_paths_from_file(
            name="meta", file_path=LOOKUP_PATH
        )
        paths.fast_forward_paths(pathsname="meta", filename="lookups")
        paths.results_manager.get_named_results("meta")
        # test the lookup
        path = paths.csvpath()
        path.parse(
            f"""
                ${PATH}[*][
                    @z1 = metaphone("zach", $meta.variables.meta)
                    @z2 = metaphone("zack", $meta.variables.meta)
                    @z = equals(@z1, @z2)

                    @s1 = metaphone("Sacks", $meta.variables.meta)
                    @s2 = metaphone("Sax", $meta.variables.meta)
                    @s = equals(@s1, @s2)

                    @i1 = metaphone("IBM", $meta.variables.meta)
                    @i2 = metaphone("I.B.M", $meta.variables.meta)
                    @i = equals(@i1, @i2)

                    @a1 = metaphone("Add", $meta.variables.meta)
                    @a2 = metaphone("Ad", $meta.variables.meta)
                    @a = equals(@a1, @a2)

                    @s21 = metaphone("Smithson", $meta.variables.meta)
                    @s22 = metaphone("Smithsun", $meta.variables.meta)
                    @s2_ = equals(@s21, @s22)
                ]
            """
        )
        path.fast_forward()
        assert path.variables["z"] is True
        assert path.variables["s"] is True
        assert path.variables["i"] is True
        assert path.variables["a"] is True
        assert path.variables["s2_"] is True
