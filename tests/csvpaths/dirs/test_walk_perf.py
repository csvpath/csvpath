import unittest
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.util.stopwatch import Stopwatch


BUCKET = "csvpath"
DIR = "testdir"


class TestWalkPerf(unittest.TestCase):
    def test_do_walks(self):
        protocol = "azure"
        bucket = "csvpath"
        dirpath = f"{protocol}://{bucket}/testdir"
        nos = Nos(dirpath)
        print(f"dirpath: {dirpath}")

        sep = nos.sep
        text = "this is the text"
        TEMP_FILE_1 = "abc_1.txt"
        TEMP_FILE_2 = f"xyz{sep}abc_2.txt"
        TEMP_FILE_3 = f"pdq{sep}abc_3.txt"
        TEMP_FILE_4 = f"xyz{sep}ijk{sep}abc_4.txt"

        paths = [
            Nos(dirpath).join(TEMP_FILE_1),
            Nos(dirpath).join(TEMP_FILE_2),
            Nos(dirpath).join(TEMP_FILE_3),
            Nos(dirpath).join(TEMP_FILE_4),
        ]
        print(f"paths are {paths}")
        for _ in paths:
            with DataFileWriter(path=_) as file:
                file.write(text)

        stopwatch = Stopwatch()

        for _ in range(0, 20):
            Nos(dirpath).listdir(recurse=True, files_only=False)
            stopwatch.click("a")

            Nos(dirpath).listdir(recurse=False, files_only=True)
            stopwatch.click("b")

            Nos(dirpath).listdir(recurse=True, files_only=False, dirs_only=True)
            stopwatch.click("c")

            Nos(f"{dirpath}{sep}xyz").listdir(recurse=False)
            stopwatch.click("d")

            Nos(f"{dirpath}{sep}xyz").listdir(recurse=False, files_only=True)
            stopwatch.click("e")

            _ = f"{dirpath}{sep}xyz"
            Nos(_).listdir(recurse=True, files_only=True)
            stopwatch.click("f")

            Nos(f"{dirpath}{sep}xyz{sep}ijk").listdir(recurse=True)
            stopwatch.click("g")

            Nos(dirpath).listdir(recurse=True, files_only=True)
            stopwatch.click("h")
