import json
import logging
import os
import unittest
from csvpath.util.line_spooler import ListLineSpooler, CsvLineSpooler
from csvpath.util.exceptions import InputException
from csvpath.util.nos import Nos

TMP_DIR = os.path.join("tests", "util", "test_resources", "tmp", "line_spooler")


class FakeCsvPath:
    def __init__(self, *, delimiter=",", quotechar='"', filename="dummy.csv"):
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.logger = logging.getLogger("fake-csvpath")

        class FakeScanner:
            pass

        self.scanner = FakeScanner()
        self.scanner.filename = filename


class FakeResult:
    def __init__(self, *, csvpath=None, data_file_path=None, instance_dir=None, run_dir=None):
        self.csvpath = csvpath
        self.data_file_path = data_file_path
        self.instance_dir = instance_dir
        self.run_dir = run_dir


class TestUtilListLineSpooler(unittest.TestCase):
    def test_requires_lines_argument(self):
        with self.assertRaises(InputException):
            ListLineSpooler(lines=None)

    def test_append_adds_to_sink(self):
        sink = []
        spooler = ListLineSpooler(lines=sink)
        spooler.append(["a", "b"])
        assert sink == [["a", "b"]]

    def test_len_reflects_sink_length(self):
        sink = [["a"], ["b"], ["c"]]
        spooler = ListLineSpooler(lines=sink)
        assert len(spooler) == 3

    def test_bytes_written_is_always_zero(self):
        spooler = ListLineSpooler(lines=[])
        spooler.append(["a", "b", "c"])
        assert spooler.bytes_written() == 0

    def test_close_is_a_noop_and_leaves_closed_false(self):
        spooler = ListLineSpooler(lines=[])
        spooler.close()
        # a memory-only spooler never actually opens/closes a file, so
        # closed intentionally stays False
        assert spooler.closed is False


class TestUtilCsvLineSpooler(unittest.TestCase):
    def setUp(self):
        nos = Nos(TMP_DIR)
        if not nos.dir_exists():
            nos.makedirs()

    def tearDown(self):
        nos = Nos(TMP_DIR)
        if nos.dir_exists():
            nos.remove()

    def _path(self, name="data.csv"):
        return os.path.join(TMP_DIR, name)

    #
    # construction / property fallbacks
    #

    def test_defaults_delimiter_and_quotechar(self):
        spooler = CsvLineSpooler(None, path=self._path())
        assert spooler.delimiter == ","
        assert spooler.quotechar == '"'

    def test_explicit_delimiter_and_quotechar_win_over_result(self):
        result = FakeResult(csvpath=FakeCsvPath(delimiter="|", quotechar="'"))
        spooler = CsvLineSpooler(result, path=self._path(), delimiter=";", quotechar="^")
        assert spooler.delimiter == ";"
        assert spooler.quotechar == "^"

    def test_delimiter_and_quotechar_fall_back_to_result_csvpath(self):
        result = FakeResult(csvpath=FakeCsvPath(delimiter="|", quotechar="'"))
        spooler = CsvLineSpooler(result, path=self._path(), delimiter=None, quotechar=None)
        assert spooler.delimiter == "|"
        assert spooler.quotechar == "'"

    def test_delimiter_returns_none_and_logs_when_nothing_available(self):
        spooler = CsvLineSpooler(None, path=self._path(), delimiter=None, quotechar=None)
        assert spooler.delimiter is None
        assert spooler.quotechar is None

    def test_logger_uses_explicit_logger_if_given(self):
        my_logger = logging.getLogger("explicit-test-logger")
        spooler = CsvLineSpooler(None, path=self._path(), logger=my_logger)
        assert spooler.logger is my_logger

    def test_logger_falls_back_to_result_csvpath_logger(self):
        fake_cp = FakeCsvPath()
        result = FakeResult(csvpath=fake_cp)
        spooler = CsvLineSpooler(result, path=self._path())
        assert spooler.logger is fake_cp.logger

    def test_logger_falls_back_to_class_logger_when_no_result(self):
        spooler = CsvLineSpooler(None, path=self._path())
        assert spooler.logger.name == "CsvLineSpooler"

    def test_path_setter_normalizes_separators(self):
        spooler = CsvLineSpooler(None, path=self._path())
        spooler.path = "tests\\util\\test_resources\\tmp\\line_spooler\\out.csv"
        assert spooler.path == "tests/util/test_resources/tmp/line_spooler/out.csv"

    #
    # _instance_data_file_path / path resolution when no explicit path given
    #

    def test_path_property_resolves_from_result_when_not_explicit(self):
        result = FakeResult(csvpath=FakeCsvPath(), data_file_path=self._path("resolved.csv"))
        spooler = CsvLineSpooler(result, path=None)
        assert spooler.path == self._path("resolved.csv")

    def test_path_property_stays_none_when_result_is_none(self):
        spooler = CsvLineSpooler(None, path=None)
        assert spooler.path is None

    def test_path_property_stays_none_when_result_csvpath_is_none(self):
        result = FakeResult(csvpath=None)
        spooler = CsvLineSpooler(result, path=None)
        assert spooler.path is None

    def test_path_property_stays_none_when_scanner_filename_is_none(self):
        result = FakeResult(csvpath=FakeCsvPath(filename=None))
        spooler = CsvLineSpooler(result, path=None)
        assert spooler.path is None

    #
    # writing
    #

    def test_append_writes_a_row_and_increments_count(self):
        spooler = CsvLineSpooler(None, path=self._path())
        spooler.append(["a", "b", "c"])
        spooler.close()
        with open(self._path(), "r", encoding="utf-8") as f:
            content = f.read()
        assert "a,b,c" in content
        assert len(spooler) == 1

    def test_append_accumulates_approximate_bytes_for_non_local_path(self):
        spooler = CsvLineSpooler(None, path="s3://bucket/key.csv")
        # avoid a real network write: swap in a fake writer directly
        written = []

        class FakeWriter:
            def writerows(self, rows):
                written.extend(rows)

        spooler.writer = FakeWriter()
        spooler.append(["a", "bb", "ccc"])
        assert spooler._aprox_bytes == len(str(["a", "bb", "ccc"]))

    def test_append_raises_when_writer_cannot_be_created(self):
        spooler = CsvLineSpooler(None, path=None)
        with self.assertRaises(InputException):
            spooler.append(["a"])

    #
    # reading
    #

    def test_to_list_returns_empty_when_no_path(self):
        spooler = CsvLineSpooler(None, path=None)
        assert spooler.to_list() == []

    def test_to_list_returns_empty_when_file_does_not_exist(self):
        spooler = CsvLineSpooler(None, path=self._path("missing.csv"))
        assert spooler.to_list() == []

    def test_to_list_reads_back_written_rows(self):
        spooler = CsvLineSpooler(None, path=self._path())
        spooler.append(["a", "b"])
        spooler.append(["c", "d"])
        spooler.close()
        reread = CsvLineSpooler(None, path=self._path())
        assert reread.to_list() == [["a", "b"], ["c", "d"]]

    def test_next_yields_written_rows(self):
        spooler = CsvLineSpooler(None, path=self._path())
        spooler.append(["x", "y"])
        spooler.close()
        reread = CsvLineSpooler(None, path=self._path())
        assert list(reread.next()) == [["x", "y"]]

    def test_next_raises_value_error_when_path_is_unset(self):
        # documents a real bug (issue #195): "if not self.path: ..." is a
        # no-op, so next() falls through to Nos(None).exists(), which
        # raises ValueError instead of returning/yielding nothing the way
        # to_list() does for the same situation.
        spooler = CsvLineSpooler(None, path=None)
        with self.assertRaises(ValueError):
            list(spooler.next())

    #
    # bytes_written
    #

    def test_bytes_written_reflects_real_file_size_when_local(self):
        spooler = CsvLineSpooler(None, path=self._path())
        spooler.append(["a", "b", "c"])
        spooler.close()
        assert spooler.bytes_written() == os.path.getsize(self._path())

    def test_bytes_written_returns_negative_one_when_local_file_missing(self):
        # bytes_written()'s except FileNotFoundError branch is effectively
        # dead: FileInfo.info() does not raise for a missing local file,
        # it returns FileInfo._empty(), whose "bytes" key is -1. So a
        # missing file yields -1, not the 0 the except branch implies.
        spooler = CsvLineSpooler(None, path=self._path("missing.csv"))
        assert spooler.bytes_written() == -1

    def test_bytes_written_returns_aprox_bytes_when_not_local(self):
        spooler = CsvLineSpooler(None, path="s3://bucket/key.csv")
        spooler._aprox_bytes = 42
        assert spooler.bytes_written() == 42

    #
    # __len__ via meta.json
    #

    def test_len_reads_count_matches_from_meta_json(self):
        meta_path = os.path.join(TMP_DIR, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"runtime_data": {"count_matches": 7}}, f)
        result = FakeResult(instance_dir=TMP_DIR)
        spooler = CsvLineSpooler(result, path=self._path())
        assert len(spooler) == 7

    def test_len_is_zero_without_result_or_meta_json(self):
        spooler = CsvLineSpooler(None, path=self._path())
        assert len(spooler) == 0

    #
    # close
    #

    def test_close_sets_closed_true_and_clears_sink(self):
        spooler = CsvLineSpooler(None, path=self._path())
        spooler.load_if()
        assert spooler.sink is not None
        spooler.close()
        assert spooler.sink is None
        assert spooler.closed is True


if __name__ == "__main__":
    unittest.main()
