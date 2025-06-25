import unittest
from csvpath import CsvPaths
from csvpath.util.sqliter import Sqliter
from csvpath.managers.integrations.sqlite.sqlite_results_listener import (
    SqliteResultsListener,
)


class TestCsvPathsSqliteBootstrap(unittest.TestCase):
    def test_sqlite_1(self):
        paths = CsvPaths()

        with Sqliter(config=paths.config, client_class=SqliteResultsListener) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            rows = cursor.fetchall()
            for row in rows:
                if row[0] == "named_paths_group_run":
                    return
            raise RuntimeError("did not find table")
