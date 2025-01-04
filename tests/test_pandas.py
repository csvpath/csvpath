import unittest
from csvpath import CsvPath
from csvpath.util.file_readers import DataFileReader

PATH = "tests/test_resources/test.csv"


class TestPandas(unittest.TestCase):
    def test_csvpaths_pandas_1(self):
        try:
            import pandas as pd
        except ImportError:
            return
        df = pd.read_csv(PATH, delimiter=",", quotechar='"', header=None)
        DataFileReader.register_data(path="pandastest", filelike=df)
        c = """
            ~
              id: pandas test
              validation-mode: no-raise, print
            ~
            $pandastest[1*][
                line(
                    string.notnone("firstname"),
                    string.notnone("lastname"),
                    string("say")
                )
                #lastname == "Bat"
            ]
        """
        lines = CsvPath().collect(c)
        assert len(lines) == 7
