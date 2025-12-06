import unittest
import os
from csvpath.csvpaths import CsvPaths
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos


BUCKET = "csvpath"
DIR = "testdir"


class TestCsvPathsBackendDirs(unittest.TestCase):
    def test_dirs(self) -> None:
        config = CsvPaths().config

        for _ in [
            ("s3", "csvpath-example-1"),
            ("gs", "csvpath-testing-1"),
            ("azure", "csvpath"),
            (
                "sftp",
                config.get(section="sftp", name="server"),
                config.get(section="sftp", name="port"),
            ),
            ("", f"tests{os.sep}test_resources"),
        ]:
            try:
                self.do_test_dirs(_)
            except Exception as e:
                raise Exception(
                    f"""ERROR: e: {type(e)}: {e}\nConfig: {config}: {config.configpath}\n_: {_}: {config.configpath}"""
                )

    def do_test_dirs(self, backend):
        print(f"doing backend {backend}")
        protocol = backend[0]
        bucket = backend[1]
        if len(backend) == 3:
            bucket = f"{bucket}:{backend[2]}"
        dirpath = None
        if protocol == "":
            dirpath = f"{bucket}{os.sep}{DIR}"
        else:
            dirpath = f"{protocol}://{bucket}/{DIR}"
        nos = Nos(dirpath)
        print(f"dirpath: {dirpath}")
        sep = nos.sep

        TEMP_FILE_1 = "abc_1.txt"
        TEMP_FILE_2 = f"xyz{sep}abc_2.txt"
        TEMP_FILE_3 = f"pdq{sep}abc_3.txt"
        TEMP_FILE_4 = f"xyz{sep}ijk{sep}abc_4.txt"

        DIR_1 = "xyz"
        DIR_2 = "pdq"
        DIR_3 = f"xyz{sep}ijk"

        print(f"checking if {nos} exists")
        if nos.exists():
            print(f"removing {nos}")
            nos.remove()
        print(f"rechecking if {nos} exists")
        assert nos.exists() is False

        text = "this is the text"
        paths = [
            Nos(dirpath).join(TEMP_FILE_1),
            Nos(dirpath).join(TEMP_FILE_2),
            Nos(dirpath).join(TEMP_FILE_3),
            Nos(dirpath).join(TEMP_FILE_4),
        ]
        print(f"paths are {paths}")

        requires_dir = protocol == "sftp" or protocol == ""
        if requires_dir:
            nos.makedirs()

        for _ in paths:
            if requires_dir:
                dpath = None
                if protocol == "sftp":
                    dpath = _[0 : _.rfind("/")] if _.rfind("/") > -1 else None
                else:
                    dpath = os.path.dirname(_)
                if dpath and not Nos(dpath).exists():
                    Nos(dpath).makedirs()
            with DataFileWriter(path=_) as file:
                print(f"writing {text}")
                file.write(text)

        print(f"1. listing {dirpath}")
        lst = Nos(dirpath).listdir(recurse=True, files_only=False)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 in lst
        assert TEMP_FILE_3 in lst
        assert TEMP_FILE_4 in lst
        assert "xyz" in lst
        assert "pdq" in lst
        assert f"xyz{sep}ijk" in lst

        print(f"2. listing {dirpath}")
        lst = Nos(dirpath).listdir(recurse=False, files_only=True)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 not in lst
        assert TEMP_FILE_3 not in lst
        assert TEMP_FILE_4 not in lst
        assert "xyz" not in lst

        print(f"3. listing {dirpath}")
        lst = Nos(dirpath).listdir(recurse=True, files_only=False, dirs_only=True)
        assert lst is not None
        assert DIR_1 in lst
        assert DIR_2 in lst
        assert DIR_3 in lst
        # these are definitely not there, but should we be asking for DIR+file?
        assert TEMP_FILE_1 not in lst
        assert TEMP_FILE_2 not in lst
        assert TEMP_FILE_3 not in lst
        assert TEMP_FILE_4 not in lst

        print(f"4. listing {dirpath}")
        lst = Nos(f"{dirpath}{sep}xyz").listdir(recurse=False)
        assert lst is not None
        assert len(lst) == 2
        assert "abc_2.txt" in lst
        assert "ijk" in lst

        print(f"5. listing {dirpath}")
        lst = Nos(f"{dirpath}{sep}xyz").listdir(recurse=False, files_only=True)
        assert lst is not None
        assert "abc_2.txt" in lst
        assert "ijk" not in lst

        _ = f"{dirpath}{sep}xyz"
        print(f"6. listing {dirpath}")
        lst = Nos(_).listdir(recurse=True, files_only=True)
        assert lst is not None
        assert len(lst) == 2
        assert f"{TEMP_FILE_4[4:]}" in lst
        assert f"{TEMP_FILE_2[4:]}" in lst

        print(f"7. listing {dirpath}")
        lst = Nos(f"{dirpath}{sep}xyz{sep}ijk").listdir(recurse=True)
        assert lst is not None
        assert len(lst) == 1
        assert f"{TEMP_FILE_4[8:]}" in lst

        print(f"8. listing {dirpath}")
        lst = Nos(dirpath).listdir(recurse=True, files_only=True)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 in lst
        assert TEMP_FILE_3 in lst
        assert TEMP_FILE_4 in lst

        # these are definitely not there, but should we be asking for DIR+file?
        assert "xyz" not in lst
        assert "pdq" not in lst
        assert "ijk" not in lst
