import unittest
from os import environ
from csvpath.csvpaths import CsvPaths
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.sftp.sftp_nos import SftpDo
from csvpath.util.sftp.sftp_walk import SftpWalk
from csvpath.util.path_util import PathUtility as pathu


paths = CsvPaths()
c = paths.config


class Paths:
    TEMP_DIR_1 = pathu.resep("tests/test_resources/test_dirs/xyz")
    TEMP_DIR_2 = pathu.resep("tests/test_resources/test_dirs/pdq")
    TEMP_DIR_3 = pathu.resep("tests/test_resources/test_dirs/xyz/ijk")

    TEMP_FILENAME_1 = "abc_1.txt"
    TEMP_FILENAME_2 = "abc_2.txt"
    TEMP_FILENAME_3 = "abc_3.txt"
    TEMP_FILENAME_4 = "abc_4.txt"

    TEMP_FILE_1 = pathu.resep("tests/test_resources/test_dirs/abc_1.txt")
    TEMP_FILE_2 = pathu.resep("tests/test_resources/test_dirs/xyz/abc_2.txt")
    TEMP_FILE_3 = pathu.resep("tests/test_resources/test_dirs/pdq/abc_3.txt")
    TEMP_FILE_4 = pathu.resep("tests/test_resources/test_dirs/xyz/ijk/abc_4.txt")

    DIRS = []
    DIRS.append(TEMP_DIR_1)
    DIRS.append(TEMP_DIR_2)
    DIRS.append(TEMP_DIR_3)

    PATHS = []
    PATHS.append(TEMP_FILE_1)
    PATHS.append(TEMP_FILE_2)
    PATHS.append(TEMP_FILE_3)
    PATHS.append(TEMP_FILE_4)

    NAMES = PATHS

    text = "this is the text"


class TestDirsLocal(unittest.TestCase):
    def test_local_crud_files(self):
        for name in Paths.PATHS:
            try:
                nos = Nos(name).remove()
            except Exception:
                ...

        for adir in Paths.DIRS:
            nos = Nos(adir)
            if not nos.exists():
                nos.makedirs()

        for path in Paths.PATHS:
            with DataFileWriter(path=path) as writer:
                writer.append(Paths.text)

        lst = Nos("tests/test_resources/test_dirs/").listdir(
            recurse=True, files_only=False
        )
        assert lst is not None
        assert Paths.TEMP_FILE_1 in lst
        assert Paths.TEMP_FILE_2 in lst
        assert Paths.TEMP_FILE_3 in lst
        assert Paths.TEMP_FILE_4 in lst
        assert pathu.resep("tests/test_resources/test_dirs/xyz") in lst
        assert pathu.resep("tests/test_resources/test_dirs/pdq") in lst
        assert pathu.resep("tests/test_resources/test_dirs/xyz/ijk") in lst

        lst = Nos("tests/test_resources/test_dirs/").listdir(
            recurse=False, files_only=True
        )
        assert lst is not None
        assert Paths.TEMP_FILENAME_1 in lst
        assert Paths.TEMP_FILENAME_2 not in lst
        assert Paths.TEMP_FILENAME_3 not in lst
        assert Paths.TEMP_FILENAME_4 not in lst
        assert "xyz" not in lst

        lst = Nos("tests/test_resources/test_dirs/").listdir(
            recurse=True, files_only=False, dirs_only=True
        )
        assert lst is not None
        assert Paths.TEMP_DIR_1 in lst
        assert Paths.TEMP_DIR_2 in lst
        assert Paths.TEMP_DIR_3 in lst
        assert Paths.TEMP_FILE_1 not in lst
        assert Paths.TEMP_FILE_2 not in lst
        assert Paths.TEMP_FILE_3 not in lst
        assert Paths.TEMP_FILE_4 not in lst

        lst = Nos("tests/test_resources/test_dirs/xyz").listdir(recurse=False)
        assert lst is not None
        assert "abc_2.txt" in lst
        assert "ijk" in lst

        lst = Nos("tests/test_resources/test_dirs/xyz").listdir(
            recurse=False, files_only=True
        )
        assert lst is not None
        assert "abc_2.txt" in lst
        assert "ijk" not in lst

        lst = Nos("tests/test_resources/test_dirs/xyz").listdir(
            recurse=True, files_only=True
        )
        assert lst is not None
        assert Paths.TEMP_FILE_4 in lst
        assert Paths.TEMP_FILE_2 in lst

        lst = Nos("tests/test_resources/test_dirs/xyz/ijk").listdir(recurse=True)
        assert lst is not None
        assert len(lst) == 1
        assert Paths.TEMP_FILE_4 in lst

        lst = Nos("tests/test_resources/test_dirs/").listdir(
            recurse=True, files_only=True
        )
        assert lst is not None
        assert Paths.TEMP_FILE_1 in lst
        assert Paths.TEMP_FILE_2 in lst
        assert Paths.TEMP_FILE_3 in lst
        assert Paths.TEMP_FILE_4 in lst
        assert "xyz" not in lst
        assert "pdq" not in lst
        assert "ijk" not in lst

        for i, name in enumerate(Paths.PATHS):
            Nos(name).remove()
            Nos(name).exists() is False

        Nos(Paths.DIRS[0]).remove()
        Nos(Paths.DIRS[0]).dir_exists() is False

        Nos(Paths.DIRS[1]).remove()
        Nos(Paths.DIRS[1]).dir_exists() is False
