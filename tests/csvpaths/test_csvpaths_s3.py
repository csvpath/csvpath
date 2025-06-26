import unittest
from os import environ
from csvpath.csvpaths import CsvPaths
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.s3.s3_utils import S3Utils
from csvpath.util.s3.s3_fingerprinter import S3Fingerprinter
from tests.csvpaths.builder import Builder

FILES = {"timezones": "s3://csvpath-example-1/timezones.csv"}
INPUTS_FILES = "s3://csvpath-example-1/inputs/named_files"
BUCKET = "csvpath-example-1"
TEMP_FILE_NAME = "abc.txt"


class TestCsvPathsS3(unittest.TestCase):
    def test_s3_add_bucket_file(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        #
        # tests that we can load a file from s3 into named_files
        #
        cs = Builder().build()
        cs.file_manager.add_named_file(
            name="timezones", path="s3://csvpath-example-1/timezones.csv"
        )
        path = '$[*][ print("$.headers.0 full name: $.headers.2")]'
        d = {"tz": [f"{path}"]}
        cs.paths_manager.set_named_paths(d)
        cs.collect_paths(filename="timezones", pathsname="tz")
        pathresults = cs.results_manager.get_named_results("tz")
        results = pathresults[0]
        valid = cs.results_manager.is_valid("tz")
        assert len(results) > 100
        assert valid

    def test_s3_read_1(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        cs = Builder().build()
        cs.file_manager.set_named_files(FILES)
        path = '$[*][ print("$.headers.0 full name: $.headers.2")]'
        d = {"tz": [f"{path}"]}
        cs.paths_manager.set_named_paths(d)
        cs.collect_paths(filename="timezones", pathsname="tz")
        pathresults = cs.results_manager.get_named_results("tz")

        results = pathresults[0]
        valid = cs.results_manager.is_valid("tz")
        assert len(results) > 100
        assert valid

    def test_s3_write_file(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        text = "this is the text"
        path = f"s3://{BUCKET}/{TEMP_FILE_NAME}"
        c = S3Utils.make_client()
        S3Utils.remove(BUCKET, TEMP_FILE_NAME, client=c)
        with DataFileWriter(path=path) as writer:
            writer.append(text)
        reader = DataFileReader(path, mode="r", encoding="utf-8")
        for s in reader.next_raw():
            assert s == text
            break
        assert S3Utils.exists(BUCKET, TEMP_FILE_NAME, client=c)
        S3Utils.remove(BUCKET, TEMP_FILE_NAME, client=c)
        assert S3Utils.exists(BUCKET, TEMP_FILE_NAME, client=c) is False

    def test_s3_generate_fingerprint(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        text = "this is the text"
        path = f"s3://{BUCKET}/{TEMP_FILE_NAME}"
        c = S3Utils.make_client()
        S3Utils.remove(BUCKET, TEMP_FILE_NAME, client=c)
        with DataFileWriter(path=path) as writer:
            writer.append(text)
        fp = S3Fingerprinter()
        h = fp.fingerprint(path)
        assert h == "463tg/4lGkYJ9mEOm8kJOxUew5rVWQvkb0DGsygsZbw="
        assert S3Utils.exists(BUCKET, TEMP_FILE_NAME, client=c)
        S3Utils.remove(BUCKET, TEMP_FILE_NAME, client=c)
        assert S3Utils.exists(BUCKET, TEMP_FILE_NAME, client=c) is False

    def test_s3_list_dir(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        text = "this is the text"
        a = f"s3://{BUCKET}/inputs/named_files/x/a"
        b = f"s3://{BUCKET}/inputs/named_files/x/b"
        c = f"s3://{BUCKET}/inputs/named_files/x/c"
        nos = Nos(None)

        nos.path = a
        nos.remove()
        nos.path = b
        nos.remove()
        nos.path = c
        nos.remove()
        with DataFileWriter(path=a) as writer:
            writer.append(text)
        # check that we're actually writing Ok. this is extra.
        reader = DataFileReader(a, mode="r", encoding="utf-8")
        for s in reader.next_raw():
            assert s == text
            break
        with DataFileWriter(path=b) as writer:
            writer.append(text)
        with DataFileWriter(path=c) as writer:
            writer.append(text)
        x = f"s3://{BUCKET}/inputs/named_files/x"
        nos.path = x
        s = nos.listdir()
        assert s
        assert len(s) == 3
        assert "a" in s
        assert "b" in s
        assert "c" in s
        nos.path = a
        nos.remove()
        nos.path = b
        nos.remove()
        nos.path = c
        nos.remove()

    def test_s3_file_exists(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        text = "this is the text"
        a = f"s3://{BUCKET}/inputs/named_files/x/a"
        Nos(a).remove()
        b = Nos(a).exists()
        assert b is False

        with DataFileWriter(path=a) as writer:
            writer.append(text)
        reader = DataFileReader(a)
        for s in reader.next_raw():
            assert s == text
            break

        b = Nos(a).exists()
        assert b is True
        Nos(a).remove()
        b = Nos(a).exists()
        assert b is False

    def test_s3_remove(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        text = "this is the text"
        x = f"s3://{BUCKET}/inputs/named_files/x"
        a = f"s3://{BUCKET}/inputs/named_files/x/a"
        b = f"s3://{BUCKET}/inputs/named_files/x/a/b"
        c = f"s3://{BUCKET}/inputs/named_files/x/a/c"
        c2 = f"s3://{BUCKET}/inputs/named_files/x/d/c"
        nos = Nos(None)
        nos.path = x
        nos.remove()

        nos.path = a
        nos.remove()
        nos.path = b
        nos.remove()
        nos.path = c
        nos.remove()

        nos.path = x
        bb = nos.exists()
        assert bb is False
        nos.path = a
        bb = nos.exists()
        assert bb is False
        nos.path = b
        bb = nos.exists()
        assert bb is False
        nos.path = c
        bb = nos.exists()
        assert bb is False

        with DataFileWriter(path=x) as writer:
            writer.append(text)
        with DataFileWriter(path=a) as writer:
            writer.append(text)
        with DataFileWriter(path=b) as writer:
            writer.append(text)
        with DataFileWriter(path=c) as writer:
            writer.append(text)

        nos.path = a
        bb = nos.isfile()
        assert bb is True

        nos.path = x
        bb = nos.exists()
        assert bb is True
        nos.path = a
        bb = nos.exists()
        assert bb is True
        nos.path = b
        bb = nos.exists()
        assert bb is True
        nos.path = c
        bb = nos.exists()
        assert bb is True

        nos.path = x
        nos.remove()
        bb = Nos(x).exists()
        assert bb is False
        nos.path = a
        bb = nos.exists()
        assert bb is False
        nos.path = b
        bb = nos.exists()
        assert bb is False
        nos.path = c
        bb = nos.exists()
        assert bb is False

        with DataFileWriter(path=c) as writer:
            writer.append(text)
        with DataFileWriter(path=c2) as writer:
            writer.append(text)
        nos.path = x
        bb = nos.dir_exists()
        assert bb is True
        nos.path = x
        bb = nos.isfile()
        assert bb is False
        nos.path = c
        bb = nos.exists()
        assert bb is True
        nos.path = c2
        bb = nos.exists()
        assert bb is True

        nos.path = x
        Nos(x).remove()
        bb = nos.exists()
        assert bb is False
        nos.path = c
        bb = nos.exists()
        assert bb is False
        nos.path = c2
        bb = nos.exists()
        assert bb is False

    def test_s3_add_named_file(self):
        if not environ.get("AWS_ACCESS_KEY_ID") or not environ.get(
            "AWS_SECRET_ACCESS_KEY"
        ):
            print(
                """
                  the test_s3_read_1 test requires AWS SK and AK env
                  vars with permission to read the file at
                  s3://csvpath-example-1/timezones.csv
                """
            )
            return
        paths = Builder().build()
        paths.config.inputs_files_path = INPUTS_FILES
        paths.file_manager.set_named_files(FILES)
