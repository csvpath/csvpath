import unittest
from csvpath.csvpaths import CsvPaths
from os import environ

FILES = {"timezones": "s3://csvpath-example-1/timezones.csv"}
NAMED_PATHS_DIR = "tests/test_resources/xlsx/named_paths"


class TestS3(unittest.TestCase):
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
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        path = '$[*][ print("$.headers.0 full name: $.headers.2")]'
        d = {"tz": [f"{path}"]}
        #
        # collect_paths is creating a wrong inputs dir directory
        #
        cs.paths_manager.set_named_paths(d)
        cs.collect_paths(filename="timezones", pathsname="tz")
        pathresults = cs.results_manager.get_named_results("tz")

        print(f"pathresults are: {len(pathresults)}")
        results = pathresults[0]
        print(f"results are: {len(results)}")
        valid = cs.results_manager.is_valid("tz")
        assert len(results) > 100
        assert valid
