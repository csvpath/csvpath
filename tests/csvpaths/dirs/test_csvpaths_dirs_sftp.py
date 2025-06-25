import unittest
from os import environ
from csvpath.csvpaths import CsvPaths
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.sftp.sftp_nos import SftpDo
from csvpath.util.sftp.sftp_walk import SftpWalk
from csvpath.util.sftp.sftp_config import SftpConfig

paths = CsvPaths()
c = paths.config
server = c.get(section="sftp", name="server")
port = c.get(section="sftp", name="port")

TEMP_DIR_1 = "xyz"
TEMP_DIR_2 = "pdq"
TEMP_DIR_3 = "xyz/ijk"

DIR_1 = "xyz"
DIR_2 = "pdq"
DIR_3 = "xyz/ijk"

TEMP_FILE_1 = "abc_1.txt"
TEMP_FILE_2 = "xyz/abc_2.txt"
TEMP_FILE_3 = "pdq/abc_3.txt"
TEMP_FILE_4 = "xyz/ijk/abc_4.txt"

DIRS = []
DIRS.append(f"sftp://{server}:{port}/{TEMP_DIR_1}")
DIRS.append(f"sftp://{server}:{port}/{TEMP_DIR_2}")
DIRS.append(f"sftp://{server}:{port}/{TEMP_DIR_3}")

PATHS = []
PATHS.append(f"sftp://{server}:{port}/{TEMP_FILE_1}")
PATHS.append(f"sftp://{server}:{port}/{TEMP_FILE_2}")
PATHS.append(f"sftp://{server}:{port}/{TEMP_FILE_3}")
PATHS.append(f"sftp://{server}:{port}/{TEMP_FILE_4}")

text = "this is the text"


class TestCsvPathsDirsSftp(unittest.TestCase):
    def _available(self):
        skip = CsvPaths().config.get(section="testing", name="sftp.skip", default="no")
        if skip.strip() == "yes":
            return False
        return SftpConfig.check_for_server(paths.config)

    def test_sftp_crud_dirs(self):
        if not self._available():
            print(
                "Cannot run test test_sftp_crud_dirs because the server is not available"
            )
            return

        for adir in DIRS:
            SftpDo(adir).makedirs()
        for path in PATHS:
            with DataFileWriter(path=path) as writer:
                writer.append(text)

        walk = SftpWalk(SftpDo(DIRS[0])._config)
        lst = walk.listdir(path="/")
        walk.remove("xyz")
        Nos(DIRS[0]).dir_exists() is False
        lst = walk.listdir(path="/")
        assert ("abc_1.txt", True) in lst
        assert ("pdq", False) in lst
        assert ("pdq/abc_3.txt", True) in lst
        nos = Nos(PATHS[0])
        nos.remove()
        nos.exists() is False
        lst = walk.listdir(path="/")
        assert ("pdq", False) in lst
        assert ("pdq/abc_3.txt", True) in lst

    def test_sftp_crud_files(self):
        if not self._available():
            print(
                "Cannot run test test_sftp_crud_files because the server is not available"
            )
            return

        for name in PATHS:
            try:
                Nos(name).remove()
            except Exception:
                ...

        for adir in DIRS:
            Nos(adir).makedirs()

        for path in PATHS:
            with DataFileWriter(path=path) as writer:
                writer.append(text)

        myserver = f"sftp://{server}:{port}"
        try:
            Nos(f"{myserver}/inputs").remove()
        except Exception:
            ...

        try:
            Nos(f"{myserver}/archive").remove()
        except Exception:
            ...

        lst = Nos(f"{myserver}/").listdir(recurse=True, files_only=False)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 in lst
        assert TEMP_FILE_3 in lst
        assert TEMP_FILE_4 in lst
        assert "xyz" in lst
        assert "pdq" in lst
        assert "xyz/ijk" in lst

        lst = Nos(f"{myserver}/").listdir(recurse=False, files_only=True)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 not in lst
        assert TEMP_FILE_3 not in lst
        assert TEMP_FILE_4 not in lst
        assert "xyz" not in lst

        lst = Nos(f"{myserver}/").listdir(
            recurse=True, files_only=False, dirs_only=True
        )
        assert lst is not None
        assert DIR_1 in lst
        assert DIR_2 in lst
        assert DIR_3 in lst
        assert TEMP_FILE_1 not in lst
        assert TEMP_FILE_2 not in lst
        assert TEMP_FILE_3 not in lst
        assert TEMP_FILE_4 not in lst

        lst = Nos(f"{myserver}/xyz").listdir(recurse=False)
        assert lst is not None
        assert "abc_2.txt" in lst
        assert "ijk" in lst
        assert "abc_4.txt" not in lst
        assert "ijk/abc_4.txt" not in lst

        lst = Nos(f"{myserver}/xyz").listdir(recurse=False, files_only=True)
        assert lst is not None
        assert "abc_2.txt" in lst
        assert "ijk" not in lst

        lst = Nos(f"{myserver}/xyz").listdir(recurse=True, files_only=True)
        assert lst is not None
        assert TEMP_FILE_4 in lst
        assert TEMP_FILE_2 in lst

        lst = Nos(f"{myserver}/xyz/ijk").listdir(recurse=True)
        assert lst is not None
        assert len(lst) == 1
        assert TEMP_FILE_4 in lst

        lst = Nos(f"{myserver}/").listdir(recurse=True, files_only=True)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 in lst
        assert TEMP_FILE_3 in lst
        assert TEMP_FILE_4 in lst
        assert "xyz" not in lst
        assert "pdq" not in lst
        assert "ijk" not in lst

        for i, name in enumerate(PATHS):
            Nos(name).remove()
            Nos(name).exists() is False

        Nos(DIRS[0]).remove()
        Nos(DIRS[0]).dir_exists() is False

        Nos(DIRS[1]).remove()
        Nos(DIRS[1]).dir_exists() is False
