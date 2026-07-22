import os
import unittest
from csvpath.util.file_readers import DataFileReader
from csvpath.util.exceptions import InputException

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

if PANDAS_AVAILABLE:
    from csvpath.util.pandas_data_reader import PandasDataReader

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestUtilPandasDataReader(unittest.TestCase):
    def tearDown(self):
        if DataFileReader.has_data():
            for k in list(DataFileReader.DATA.keys()):
                DataFileReader.deregister_data(k)

    def test_construct_without_registered_dataframe_has_none_frame(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        reader = PandasDataReader("no-such-key")
        assert reader.dataframe is None

    def test_construct_defaults_delimiter_and_quotechar(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        reader = PandasDataReader("no-such-key")
        assert reader._delimiter == ","
        assert reader._quotechar == '"'

    def test_construct_honors_explicit_delimiter_and_quotechar(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        reader = PandasDataReader("no-such-key", delimiter="|", quotechar="'")
        assert reader._delimiter == "|"
        assert reader._quotechar == "'"

    def test_construct_picks_up_pre_registered_dataframe(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        df = pd.DataFrame([["a", "1"], ["b", "2"]])
        DataFileReader.register_data(path="pdreader-test", filelike=df)
        reader = PandasDataReader("pdreader-test")
        assert reader.dataframe is df

    def test_dataframe_setter_replaces_frame(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        reader = PandasDataReader("no-such-key")
        df = pd.DataFrame([["a", "1"]])
        reader.dataframe = df
        assert reader.dataframe is df

    def test_load_if_is_a_noop(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        reader = PandasDataReader("no-such-key")
        # unlike DataFileReader.load_if(), this never opens a file source
        reader.load_if()
        assert reader.source is None

    def test_next_raises_input_exception_when_no_dataframe_registered(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        reader = PandasDataReader("no-such-key")
        with self.assertRaises(InputException):
            list(reader.next())

    def test_next_yields_rows_as_lists(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        df = pd.DataFrame([["a", 1], ["b", 2]], columns=["letter", "number"])
        reader = PandasDataReader("no-such-key")
        reader.dataframe = df
        lines = list(reader.next())
        assert lines == [["a", 1], ["b", 2]]

    def test_next_does_not_mutate_the_registered_dataframe(self):
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        df = pd.DataFrame([["a", 1]], columns=["letter", "number"])
        reader = PandasDataReader("no-such-key")
        reader.dataframe = df
        list(reader.next())
        assert reader.dataframe.equals(df)

    def test_factory_dispatches_to_pandas_data_reader_for_registered_dataframe(self):
        # exercises DataFileReader.__new__'s dispatch logic: a path with a
        # pre-registered pandas DataFrame is routed to PandasDataReader
        # rather than CsvDataReader/XlsxReaderHelper/etc.
        if not PANDAS_AVAILABLE:
            print("Pandas is not installed. Test will be skipped.")
            return
        df = pd.read_csv(PATH, delimiter=",", quotechar='"', header=None)
        DataFileReader.register_data(path="pdreader-factory-test", filelike=df)
        reader = DataFileReader("pdreader-factory-test")
        assert isinstance(reader, PandasDataReader)


if __name__ == "__main__":
    unittest.main()
