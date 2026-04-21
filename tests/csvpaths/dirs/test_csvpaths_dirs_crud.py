import unittest
import os
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath import CsvPaths

BUCKET = "csvpath"
DIR = "testdir"
FILE = "testfile.txt"
TEXT = "this is the text"


class TestCsvPathsBackendCrud(unittest.TestCase):
    def test_backends_simple_crud(self) -> None:
        paths = CsvPaths()
        config = paths.config
        for _ in [
            ("azure", "csvpath"),
            ("gs", "csvpath-testing-1"),
            ("s3", "csvpath-example-1"),
            (
                "sftp",
                config.get(section="sftp", name="server"),
                config.get(section="sftp", name="port"),
            ),
            ("", f"tests{os.sep}test_resources"),
        ]:
            self.do_test(paths, _)

    def do_test(self, paths: CsvPaths, backend: tuple):
        import time

        start = time.perf_counter()
        print(f"\n\nstart time: {start}: {backend[0]}")
        protocol = backend[0]
        bucket = backend[1]
        if len(backend) == 3:
            bucket = f"{bucket}:{backend[2]}"
        dirpath = None
        filepath = None
        if protocol == "":
            dirpath = f"{bucket}{os.sep}{DIR}"
            filepath = f"{bucket}{os.sep}{DIR}/{FILE}"
        else:
            dirpath = f"{protocol}://{bucket}/{DIR}"
            filepath = f"{protocol}://{bucket}/{DIR}/{FILE}"
        print("")
        print(f"time 1: {time.perf_counter() - start}")
        print(f"dirpath: {dirpath}")
        exists = Nos(dirpath).dir_exists()
        print(f"time 2: {time.perf_counter() - start}")
        if Nos(dirpath).dir_exists():
            Nos(dirpath).remove()
        print(f"time 3: {time.perf_counter() - start}")
        #
        # this will be misleading for gs, azure, s3
        #
        exists = Nos(dirpath).dir_exists()
        print(f"time 4: {time.perf_counter() - start}")
        #
        # this will be misleading for gs, azure, s3
        #
        assert exists is False
        #
        # Azure only works with blobs, not real "physical" dirs. this
        # method call is a no-op.
        #
        Nos(dirpath).makedirs()
        print(f"time 5: {time.perf_counter() - start}")
        #
        # while Azure doesn't need a dir to exist, we need for there to
        # be no file occupying the space where we want a dir to "exist"
        #
        if protocol == "sftp" or protocol == "":
            assert Nos(dirpath).exists() is True
        else:
            assert Nos(dirpath).exists() is False
        print(f"time 6: {time.perf_counter() - start}")
        #
        # for the same reason, we don't say a dir exists, even when we
        # specify we are looking for a dir, unless there is at least one
        # file somewhere below the path we ask about.
        #
        if protocol == "sftp" or protocol == "":
            assert Nos(dirpath).dir_exists() is True
        else:
            assert Nos(dirpath).dir_exists() is False
        print(f"time 7: {time.perf_counter() - start}")
        #
        # write a short text to the filepath
        #
        with DataFileWriter(path=filepath) as file:
            file.write(TEXT)
        print(f"time 8: {time.perf_counter() - start}")
        assert Nos(filepath).exists() is True
        print(f"time 9: {time.perf_counter() - start}")
        #
        # because a file blob exists, the "directory" it lives in must
        # exist. sftp will have a physical dir.
        #
        exists = Nos(dirpath).dir_exists()
        print(f"time 10: {time.perf_counter() - start}")
        assert exists is True

        with DataFileReader(filepath) as file:
            txt = file.read()
            assert txt == TEXT
        print(f"time 11: {time.perf_counter() - start}")
