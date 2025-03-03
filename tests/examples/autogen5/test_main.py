import unittest
import os
from csvpath import CsvPaths
from csvpath.util.sqliter import Sqliter
from csvpath.managers.integrations.sqlite.sqlite_result_listener import (
    SqliteResultListener,
)


class TestCache(unittest.TestCase):
    def test_autogen5_example_run(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(
            name="autogen5",
            file_path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}accountants.csvpath",
        )
        paths.file_manager.add_named_file(
            name="accounts",
            path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}Washington_State_Certified_Public_Accountants.csv",
        )
        paths.fast_forward_paths(pathsname="autogen5", filename="accounts")

    def test_autogen5_paths_load_only(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(
            name="autogen5",
            file_path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}accountants.csvpath",
        )

    def test_autogen5_paths_by_json(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_json(
            f"tests{os.sep}examples{os.sep}autogen5{os.sep}two.json"
        )

    def test_autogen5_file_load_only(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="accounts",
            path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}Washington_State_Certified_Public_Accountants.csv",
        )

    def test_autogen5_sqlite_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        groups = paths.config.get(section="listeners", name="groups")
        #
        # use config direct so no save happens
        #
        paths.config.add_to_config("listeners", "groups", "sqlite")
        #
        #
        #
        paths.paths_manager.add_named_paths_from_file(
            name="autogen5",
            file_path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}accountants.csvpath",
        )
        paths.file_manager.add_named_file(
            name="accounts",
            path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}Washington_State_Certified_Public_Accountants.csv",
        )
        paths.fast_forward_paths(pathsname="autogen5", filename="accounts")
        #
        # reset listeners for other tests
        #
        paths.config.add_to_config("listeners", "groups", groups)

        with Sqliter(config=paths.config, client_class=SqliteResultListener) as conn:
            ...
            uuid = paths.run_metadata.uuid_string
            assert uuid is not None
            cursor = conn.cursor()
            rows = cursor.execute(
                f"select * from named_paths_group_run where uuid = '{uuid}'"
            )
            rows = rows.fetchmany()
            f = 0
            for row in rows:
                print(f"trow: {row}")
                f += 1
            assert f == 1
            assert rows[0][2].endswith("archive")
            tc = rows[0][3]
            assert tc is not None and tc.strip() != ""
            assert rows[0]["all_completed"] == "Y"
            assert rows[0]["all_valid"] == "Y"
            assert rows[0]["all_expected_files"] == "Y"
            assert rows[0]["error_count"] == 0
            assert rows[0]["by_line_run"] == "N"
            assert rows[0]["named_paths_name"] == rows[0]["named_results_name"]
            assert rows[0]["named_file_name"] == "accounts"
            assert (
                rows[0]["named_file_home"]
                == f"{paths.config.get(section='inputs', name='files')}{os.sep}accounts"
            )

            rows = cursor.execute(
                f"""
                select *
                from instance_run ir, named_paths_group_run gr
                where gr.uuid = '{uuid}' and ir.group_run_uuid = gr.uuid"""
            )
            rows = rows.fetchmany()
            assert len(rows) == 1
            assert rows[0]["instance_identity"] == "General data integrity checks"
            assert (
                rows[0]["number_of_files_expected"]
                == rows[0]["number_of_files_generated"]
                == 3
            )
            assert rows[0]["valid"] == "Y"
            assert rows[0]["completed"] == "Y"
            assert rows[0]["error_count"] == 0
