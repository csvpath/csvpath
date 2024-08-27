import unittest
import pytest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsTally(unittest.TestCase):
    def test_function_tally1(self):
        path = CsvPath()
        Save._save(path, "test_function_subtract")
        path.parse(f"${PATH}[*][tally(#lastname) no()] ")
        path.collect()
        print(f"test_function_tally1: path vars: {path.variables}")
        assert path.variables["lastname"]["Bat"] == 7

    def test_function_tally2(self):
        path = CsvPath()
        Save._save(path, "test_function_tally2")
        path.parse(f"${PATH}[*][tally(#firstname, #lastname)] ")
        path.collect()
        print(f"test_function_tally2: path vars: {path.variables}")
        assert path.variables["tally"]["Frog|Bat"] == 2

    def test_function_tally3(self):
        path = CsvPath()
        Save._save(path, "test_function_tally3")
        path.parse(
            f"""${PATH}[*][
                            or( #firstname == "Frog", #firstname == "Ants" )
                            tally.sothere.onmatch(#firstname, #lastname)
                        ]
                    """
        )
        path.collect()
        print(f"test_function_tally3: path vars: {path.variables}")
        assert path.variables["sothere"]["Frog|Bat"] == 2
        assert len(path.variables["firstname"]) == 2

    def test_function_tally4(self):
        path = CsvPath()
        Save._save(path, "test_function_tally4")
        path.parse(
            f"""${PATH}[*]
                            [
                                tally(#lastname) no()
                                @hmmm = @lastname.Bat
                                @ohhh = @hmmm.fish
                                @lastname.Bat = "fred"
                            ]
                   """
        )
        with pytest.raises(TypeError):
            path.collect()
            print(f"test_function_tally4: path vars: {path.variables}")
            assert path.variables["lastname"]["Bat"] == "fred"
            assert path.variables["hmmm"] == 7
            assert path.variables["ohhh"] is None
