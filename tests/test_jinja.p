import unittest
from csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"



class TestJinja(unittest.TestCase):


    def test_function_jinja(self):
        path = CsvPath()
        Save._save(path, "test_function_jinja")
        out = "tests/test_resources/out.txt"
        inf = "tests/test_resources/in.txt"
        path.parse(
            f""" ${PATH}[*][ yes()
                             last.nocontrib() -> jinja("{inf}", "{out}")
            ]
            """
        )
        print("")
        path.fast_forward()
        print(f"test_function_jinja: path vars: {path.variables}")
        with open(out, "r") as file:
            txt = file.read()
            i = txt.find("scan count: 9")
            assert i >= 0
