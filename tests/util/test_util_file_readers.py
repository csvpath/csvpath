import os
import unittest
from unittest.mock import patch
from csvpath.util.file_readers import DataFileReader, CsvDataReader
from csvpath.util.hasher import Hasher
from csvpath.util.exceptions import InputException

CSV_PATH = os.path.join("tests", "util", "test_resources", "test.csv")
XLSX_PATH = os.path.join("tests", "util", "test_resources", "xlsx", "Table_1.1_Primary_Energy_Overview.xlsx")
JSONL_PATH = os.path.join("tests", "util", "test_resources", "test.jsonl")


class TestUtilFileReaders(unittest.TestCase):
    def tearDown(self):
        if DataFileReader.has_data():
            for k in list(DataFileReader.DATA.keys()):
                DataFileReader.deregister_data(k)

    #
    # DataFileReader.__new__ dispatch
    #

    def test_new_returns_csv_data_reader_for_plain_local_path(self):
        reader = DataFileReader(CSV_PATH)
        assert isinstance(reader, CsvDataReader)

    def test_new_returns_xlsx_data_reader_for_xlsx_path(self):
        reader = DataFileReader(XLSX_PATH)
        assert type(reader).__name__ == "XlsxDataReader"

    def test_new_returns_json_data_reader_for_jsonl_path(self):
        reader = DataFileReader(JSONL_PATH)
        assert type(reader).__name__ == "JsonDataReader"

    def test_new_raises_for_hash_fragment_on_plain_csv_path(self):
        # DataFileReader.__new__ strips any "#..." fragment before
        # constructing CsvDataReader internally, but Python's __new__/
        # __init__ protocol then automatically calls __init__ a second
        # time on the returned instance using the ORIGINAL, unstripped
        # outer-call arguments (since CsvDataReader is a subclass of the
        # DataFileReader that was actually invoked). That second call
        # re-raises InputException from the raw "#"-containing path.
        # XlsxDataReader defends against this same double-init quirk by
        # re-stripping "#" itself in __init__ (see xlsx_data_reader.py);
        # CsvDataReader does not need to, since a CSV is never supposed
        # to have a "#" fragment in the first place.
        with self.assertRaises(InputException):
            DataFileReader(f"{CSV_PATH}#Sheet1")

    def test_new_dispatches_to_s3_reader_via_class_loader(self):
        with patch("csvpath.util.file_readers.ClassLoader.load") as m:
            m.return_value = "fake-s3-reader"
            reader = DataFileReader("s3://bucket/key.csv")
            assert reader == "fake-s3-reader"
            args, kwargs = m.call_args
            assert "S3DataReader" in args[0]
            assert kwargs["args"] == ["s3://bucket/key.csv"]

    def test_new_dispatches_to_sftp_reader_via_class_loader(self):
        with patch("csvpath.util.file_readers.ClassLoader.load") as m:
            m.return_value = "fake-sftp-reader"
            reader = DataFileReader("sftp://host/key.csv")
            assert reader == "fake-sftp-reader"
            assert "SftpDataReader" in m.call_args[0][0]

    def test_new_dispatches_to_azure_reader_via_class_loader(self):
        with patch("csvpath.util.file_readers.ClassLoader.load") as m:
            m.return_value = "fake-azure-reader"
            reader = DataFileReader("azure://container/key.csv")
            assert reader == "fake-azure-reader"
            assert "AzureDataReader" in m.call_args[0][0]

    def test_new_dispatches_to_gcs_reader_via_class_loader(self):
        with patch("csvpath.util.file_readers.ClassLoader.load") as m:
            m.return_value = "fake-gcs-reader"
            reader = DataFileReader("gs://bucket/key.csv")
            assert reader == "fake-gcs-reader"
            assert "GcsDataReader" in m.call_args[0][0]

    def test_new_dispatches_to_http_reader_via_class_loader(self):
        with patch("csvpath.util.file_readers.ClassLoader.load") as m:
            m.return_value = "fake-http-reader"
            reader = DataFileReader("https://example.com/key.csv")
            assert reader == "fake-http-reader"
            assert "HttpDataReader" in m.call_args[0][0]

    #
    # CsvDataReader construction
    #

    def test_csv_data_reader_none_path_raises_value_error(self):
        with self.assertRaises(ValueError):
            CsvDataReader(None)

    def test_csv_data_reader_direct_construction_rejects_hash_in_path(self):
        with self.assertRaises(InputException):
            CsvDataReader(f"{CSV_PATH}#Sheet1")

    def test_csv_data_reader_direct_construction_rejects_sheet_kwarg(self):
        with self.assertRaises(InputException):
            CsvDataReader(CSV_PATH, sheet="Sheet1")

    def test_csv_data_reader_defaults_delimiter_and_quotechar(self):
        reader = CsvDataReader(CSV_PATH)
        assert reader._delimiter == ","
        assert reader._quotechar == '"'

    def test_csv_data_reader_path_setter_normalizes_separators(self):
        reader = CsvDataReader("tests\\util\\test_resources\\test.csv")
        assert reader.path == "tests/util/test_resources/test.csv"

    #
    # reading
    #

    def test_csv_data_reader_next_yields_parsed_rows(self):
        reader = CsvDataReader(CSV_PATH)
        rows = list(reader.next())
        assert rows[0] == ["firstname", "lastname", "say"]
        assert rows[1] == ["David", "Kermit", "hi!"]
        assert len(rows) == 9

    def test_csv_data_reader_next_honors_custom_delimiter(self):
        reader = CsvDataReader(CSV_PATH, delimiter=";")
        rows = list(reader.next())
        # with the wrong delimiter the whole line is one field
        assert rows[1] == ["David,Kermit,hi!"]

    def test_next_raw_yields_raw_text_lines(self):
        reader = CsvDataReader(CSV_PATH)
        lines = list(reader.next_raw())
        assert lines[0].strip() == "firstname,lastname,say"
        assert len(lines) == 9

    #
    # source/sink lifecycle
    #

    def test_load_if_opens_source_once(self):
        reader = CsvDataReader(CSV_PATH)
        reader.load_if()
        first = reader.source
        reader.load_if()
        assert reader.source is first
        reader.close()

    def test_read_returns_full_content_and_closes_source(self):
        reader = CsvDataReader(CSV_PATH)
        content = reader.read()
        assert "firstname,lastname,say" in content
        assert reader.source is None

    def test_close_when_source_is_none_is_a_noop(self):
        reader = CsvDataReader(CSV_PATH)
        reader.close()  # should not raise
        assert reader.source is None

    def test_context_manager_opens_and_closes_source(self):
        with CsvDataReader(CSV_PATH) as reader:
            assert reader.source is not None
        assert reader.source is None

    def test_is_binary_reflects_mode(self):
        reader = CsvDataReader(CSV_PATH, mode="rb")
        assert reader.is_binary is True
        reader = CsvDataReader(CSV_PATH, mode="r")
        assert reader.is_binary is False

    #
    # metadata
    #

    def test_fingerprint_matches_hasher_output(self):
        reader = CsvDataReader(CSV_PATH)
        assert reader.fingerprint() == Hasher().hash(CSV_PATH)

    def test_file_info_returns_local_stat_shape(self):
        reader = CsvDataReader(CSV_PATH)
        info = reader.file_info()
        assert info["bytes"] == os.path.getsize(CSV_PATH)

    def test_exists_is_broken_and_always_returns_none(self):
        # documents a real bug (issue #193): DataFileReader.exists()
        # computes os.path.exists(path) but never returns it, so it
        # always evaluates to None regardless of whether the file
        # exists. zero callers anywhere in the package.
        reader = CsvDataReader(CSV_PATH)
        assert reader.exists(CSV_PATH) is None
        assert reader.exists("does-not-exist-at-all.csv") is None


if __name__ == "__main__":
    unittest.main()
