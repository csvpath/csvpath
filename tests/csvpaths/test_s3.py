import unittest
import os
from csvpath import CsvPaths
from csvpath.util.file_readers import DataFileReader


class TestS3NoEnv(unittest.TestCase):

    #
    # this test should always pass -- it is basically a manual test
    # pretending to be a unit test. the check is that DataFileReader's
    # s3 version can find its creds in env.json, which had given it
    # trouble.
    #
    def test_s3_without_os_env_creds(self) -> None:
        ak = os.environ["AWS_ACCESS_KEY_ID"]
        sk = os.environ["AWS_SECRET_ACCESS_KEY"]
        try:
            del os.environ["AWS_ACCESS_KEY_ID"]
            del os.environ["AWS_SECRET_ACCESS_KEY"]
            paths = CsvPaths()
            #
            # reach out to AWS for a file here, relying on just env.json
            #
            config = paths.config
            config.add_to_config("config", "allow_var_sub", "yes")
            #
            # env.json is outside of test and not in git
            #
            config.add_to_config("config", "var_sub_source", "keep_out_of_git_env.json")
            with DataFileReader(
                "s3://csvpath-example-1/inputs/named_paths/orders/group.csvpaths"
            ) as file:
                assert file.read() is not None
        except Exception as e:
            print(f"error: {type(e)}: {e}")
            print("have you loaded exports.sh?")
        os.environ["AWS_ACCESS_KEY_ID"] = ak
        os.environ["AWS_SECRET_ACCESS_KEY"] = sk
