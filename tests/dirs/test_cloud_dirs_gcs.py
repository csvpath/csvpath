import unittest
from os import environ
from csvpath import CsvPaths
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.gcs.gcs_utils import GcsUtility

BUCKET = "csvpath_dev"
TEMP_FILE_1 = "abc_1.txt"
TEMP_FILE_2 = "xyz/abc_2.txt"
TEMP_FILE_3 = "pdq/abc_3.txt"
TEMP_FILE_4 = "xyz/ijk/abc_4.txt"

DIR_1 = "xyz"
DIR_2 = "pdq"
DIR_3 = "xyz/ijk"

PATHS = []
PATHS.append(f"gs://{BUCKET}/{TEMP_FILE_1}")
PATHS.append(f"gs://{BUCKET}/{TEMP_FILE_2}")
PATHS.append(f"gs://{BUCKET}/{TEMP_FILE_3}")
PATHS.append(f"gs://{BUCKET}/{TEMP_FILE_4}")

NAMES = []
NAMES.append(TEMP_FILE_1)
NAMES.append(TEMP_FILE_2)
NAMES.append(TEMP_FILE_3)
NAMES.append(TEMP_FILE_4)


class TestCloudDirsGcs(unittest.TestCase):
    def test_gs_crud(self):
        if not environ.get("GCS_CREDENTIALS_PATH"):
            print(
                """
                  Google Cloud Storage tests require a connection string env var
                  with permission to read files in gs://csvpath_dev/
            """
            )
            return

        skip = CsvPaths().config.get(section="testing", name="gcs.skip", default="no")
        if skip.strip() == "yes":
            return

        text = "this is the text"

        GcsUtility.make_client()
        for name in NAMES:
            try:
                GcsUtility.remove(BUCKET, name)
            except Exception:
                ...

        for path in PATHS:
            with DataFileWriter(path=path) as writer:
                writer.append(text)

        lst = Nos(f"gs://{BUCKET}/").listdir(recurse=True, files_only=False)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 in lst
        assert TEMP_FILE_3 in lst
        assert TEMP_FILE_4 in lst
        assert "xyz" in lst
        assert "pdq" in lst
        assert "xyz/ijk" in lst

        lst = Nos(f"gs://{BUCKET}/").listdir(recurse=False, files_only=True)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 not in lst
        assert TEMP_FILE_3 not in lst
        assert TEMP_FILE_4 not in lst
        assert "xyz" not in lst

        lst = Nos(f"gs://{BUCKET}/").listdir(
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

        lst = Nos(f"gs://{BUCKET}/xyz").listdir(recurse=False)
        assert lst is not None
        assert len(lst) == 2
        assert "abc_2.txt" in lst
        assert "ijk" in lst

        lst = Nos(f"gs://{BUCKET}/xyz").listdir(recurse=False, files_only=True)
        assert lst is not None
        assert "abc_2.txt" in lst
        assert "ijk" not in lst

        lst = Nos(f"gs://{BUCKET}/xyz").listdir(recurse=True, files_only=True)
        assert lst is not None
        assert len(lst) == 2
        assert TEMP_FILE_4 in lst
        assert TEMP_FILE_2 in lst

        lst = Nos(f"gs://{BUCKET}/xyz/ijk").listdir(recurse=True)
        assert lst is not None
        assert len(lst) == 1
        assert TEMP_FILE_4 in lst

        lst = Nos(f"gs://{BUCKET}/").listdir(recurse=True, files_only=True)
        assert lst is not None
        assert TEMP_FILE_1 in lst
        assert TEMP_FILE_2 in lst
        assert TEMP_FILE_3 in lst
        assert TEMP_FILE_4 in lst
        assert "xyz" not in lst
        assert "pdq" not in lst
        assert "ijk" not in lst

        for name in NAMES:
            GcsUtility.remove(BUCKET, name)
            GcsUtility.exists(BUCKET, name) is False
