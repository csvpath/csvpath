import os
import unittest
from unittest.mock import patch
from csvpath.util.file_writers import DataFileWriter, GeneralDataWriter
from csvpath.util.file_info import FileInfo
from csvpath.util.nos import Nos

TMP_DIR = os.path.join("tests", "util", "test_resources", "tmp", "file_writers")
TMP_FILE = os.path.join(TMP_DIR, "out.csv")


class TestUtilFileWriters(unittest.TestCase):
    def setUp(self):
        nos = Nos(TMP_DIR)
        if not nos.dir_exists():
            nos.makedirs()

    def tearDown(self):
        nos = Nos(TMP_DIR)
        if nos.dir_exists():
            nos.remove()

    #
    # DataFileWriter.__new__ dispatch
    #

    def test_new_returns_general_data_writer_for_plain_local_path(self):
        writer = DataFileWriter(path=TMP_FILE)
        assert isinstance(writer, GeneralDataWriter)

    def test_new_dispatches_to_s3_writer_via_class_loader(self):
        with patch("csvpath.util.file_writers.ClassLoader.load") as m:
            m.return_value = "fake-s3-writer"
            writer = DataFileWriter(path="s3://bucket/key.csv")
            assert writer == "fake-s3-writer"
            assert "S3DataWriter" in m.call_args[0][0]
            assert m.call_args[1]["kwargs"]["path"] == "s3://bucket/key.csv"

    def test_new_dispatches_to_sftp_writer_via_class_loader(self):
        with patch("csvpath.util.file_writers.ClassLoader.load") as m:
            m.return_value = "fake-sftp-writer"
            writer = DataFileWriter(path="sftp://host/key.csv")
            assert writer == "fake-sftp-writer"
            assert "SftpDataWriter" in m.call_args[0][0]

    def test_new_dispatches_to_azure_writer_via_class_loader(self):
        with patch("csvpath.util.file_writers.ClassLoader.load") as m:
            m.return_value = "fake-azure-writer"
            writer = DataFileWriter(path="azure://container/key.csv")
            assert writer == "fake-azure-writer"
            assert "AzureDataWriter" in m.call_args[0][0]

    def test_new_dispatches_to_gcs_writer_via_class_loader(self):
        with patch("csvpath.util.file_writers.ClassLoader.load") as m:
            m.return_value = "fake-gcs-writer"
            writer = DataFileWriter(path="gs://bucket/key.csv")
            assert writer == "fake-gcs-writer"
            assert "GcsDataWriter" in m.call_args[0][0]

    #
    # GeneralDataWriter construction
    #

    def test_general_data_writer_requires_path_as_keyword(self):
        # regression test: GeneralDataWriter.__init__ used to declare path
        # as positional, but the inherited DataFileWriter.__new__ requires
        # path as keyword-only, so GeneralDataWriter(some_path) crashed
        # with TypeError at construction. Fixed by making __init__'s path
        # keyword-only too, matching the project convention of keyword
        # args for anything beyond a single obviously-required parameter.
        with self.assertRaises(TypeError):
            GeneralDataWriter(TMP_FILE)
        writer = GeneralDataWriter(path=TMP_FILE)
        assert writer.path == TMP_FILE

    def test_general_data_writer_defaults_mode_and_encoding(self):
        writer = GeneralDataWriter(path=TMP_FILE)
        assert writer.mode == "w"
        assert writer.encoding == "utf-8"

    def test_general_data_writer_path_setter_normalizes_separators(self):
        writer = GeneralDataWriter(
            path="tests\\util\\test_resources\\tmp\\file_writers\\out.csv"
        )
        assert writer.path == "tests/util/test_resources/tmp/file_writers/out.csv"

    #
    # writing
    #

    def test_write_creates_file_with_content(self):
        writer = GeneralDataWriter(path=TMP_FILE)
        writer.write("a,b,c\n1,2,3\n")
        with open(TMP_FILE, "r", encoding="utf-8") as f:
            assert f.read() == "a,b,c\n1,2,3\n"

    def test_write_in_text_mode_overwrites_existing_content(self):
        writer = GeneralDataWriter(path=TMP_FILE)
        writer.write("first\n")
        writer.write("second\n")
        with open(TMP_FILE, "r", encoding="utf-8") as f:
            assert f.read() == "second\n"

    def test_write_in_binary_mode(self):
        writer = GeneralDataWriter(path=TMP_FILE, mode="wb")
        writer.write(b"binary-data")
        with open(TMP_FILE, "rb") as f:
            assert f.read() == b"binary-data"

    def test_write_in_binary_mode_encodes_str_data(self):
        writer = GeneralDataWriter(path=TMP_FILE, mode="wb")
        writer.write("text-as-bytes")
        with open(TMP_FILE, "rb") as f:
            assert f.read() == b"text-as-bytes"

    def test_append_only_appends_in_append_mode(self):
        writer = GeneralDataWriter(path=TMP_FILE, mode="a")
        writer.append("line1\n")
        writer.append("line2\n")
        writer.close()
        with open(TMP_FILE, "r", encoding="utf-8") as f:
            assert f.read() == "line1\nline2\n"

    def test_append_with_write_mode_overwrites_despite_the_name(self):
        # documents real behavior: append() only actually appends when
        # mode is "a"/"ab" -- with the default "w" mode each append() call
        # rewrites the file from scratch, per the comment in append().
        writer = GeneralDataWriter(path=TMP_FILE, mode="w")
        writer.append("first\n")
        writer.close()
        writer2 = GeneralDataWriter(path=TMP_FILE, mode="w")
        writer2.append("second\n")
        writer2.close()
        with open(TMP_FILE, "r", encoding="utf-8") as f:
            assert f.read() == "second\n"

    #
    # sink lifecycle
    #

    def test_load_if_opens_sink_once(self):
        writer = GeneralDataWriter(path=TMP_FILE)
        writer.load_if()
        first = writer.sink
        writer.load_if()
        assert writer.sink is first
        writer.close()

    def test_close_when_sink_is_none_is_a_noop(self):
        writer = GeneralDataWriter(path=TMP_FILE)
        writer.close()  # should not raise
        assert writer.sink is None

    def test_context_manager_opens_and_closes_sink(self):
        with GeneralDataWriter(path=TMP_FILE) as writer:
            assert writer.sink is not None
        assert writer.sink is None

    def test_is_binary_reflects_mode(self):
        writer = GeneralDataWriter(path=TMP_FILE, mode="wb")
        assert writer.is_binary is True
        writer = GeneralDataWriter(path=TMP_FILE, mode="w")
        assert writer.is_binary is False

    #
    # metadata
    #

    def test_file_info_returns_local_stat_shape_after_write(self):
        writer = GeneralDataWriter(path=TMP_FILE)
        writer.write("abc")
        info = writer.file_info()
        assert info["bytes"] == os.path.getsize(TMP_FILE)

    def test_file_info_returns_empty_shape_when_file_does_not_exist(self):
        writer = GeneralDataWriter(path=os.path.join(TMP_DIR, "never-written.csv"))
        assert writer.file_info() == FileInfo._empty()


if __name__ == "__main__":
    unittest.main()
