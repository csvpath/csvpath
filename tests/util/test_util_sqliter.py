import os
import sqlite3
import unittest
from csvpath.util.sqliter import Sqliter
from csvpath.managers.integrations.sqlite.sqlite_result_listener import (
    SqliteResultListener,
)
from csvpath.util.nos import Nos

TMP_DIR = os.path.join("tests", "util", "test_resources", "tmp", "sqliter")
DB_FILE = os.path.join(TMP_DIR, "test.db")


class FakeConfig:
    def __init__(self, db_path):
        self._db_path = db_path

    def get(self, *, section, name, default=None):
        assert section == "sqlite"
        assert name == "db"
        return self._db_path


class TestUtilSqliter(unittest.TestCase):
    def setUp(self):
        nos = Nos(TMP_DIR)
        if not nos.dir_exists():
            nos.makedirs()

    def tearDown(self):
        nos = Nos(TMP_DIR)
        if nos.dir_exists():
            nos.remove()

    def _table_exists(self, db_path, table_name) -> bool:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    def test_db_file_creates_file_and_runs_schema_when_missing(self):
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config, client_class=SqliteResultListener)
        assert not os.path.exists(DB_FILE)
        path = sq.db_file
        assert path == DB_FILE
        assert os.path.exists(DB_FILE)
        assert self._table_exists(DB_FILE, "named_paths_group_run")

    def test_db_file_does_not_rerun_schema_when_file_already_exists(self):
        # pre-create an empty file so db_file's existence check
        # short-circuits before _setup_db() ever runs
        open(DB_FILE, "w").close()
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config, client_class=SqliteResultListener)
        path = sq.db_file
        assert path == DB_FILE
        assert self._table_exists(DB_FILE, "named_paths_group_run") is False

    def test_db_file_is_cached_on_the_instance(self):
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config, client_class=SqliteResultListener)
        first = sq.db_file
        # mutate config to point elsewhere; the cached value should not change
        config._db_path = os.path.join(TMP_DIR, "other.db")
        second = sq.db_file
        assert first == second == DB_FILE

    def test_default_client_class_cannot_find_its_own_schema(self):
        # documents a real gotcha (issue #197): client_class defaults to
        # type(self) (Sqliter itself), whose module directory
        # (csvpath/util/) has no schema.sql -- the real schema lives next
        # to the actual callers (SqliteResultListener, etc), which always
        # pass client_class explicitly. Omitting client_class only works
        # if the target db already exists; creating a new one without it
        # raises FileNotFoundError instead of doing anything useful.
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config)
        with self.assertRaises(FileNotFoundError):
            sq.db_file

    def test_connection_returns_sqlite_connection_and_caches_it(self):
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config, client_class=SqliteResultListener)
        conn1 = sq.connection
        conn2 = sq.connection
        assert conn1 is conn2
        assert isinstance(conn1, sqlite3.Connection)
        conn1.close()

    def test_context_manager_returns_connection_with_row_factory(self):
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config, client_class=SqliteResultListener)
        with sq as conn:
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory is sqlite3.Row

    def test_exit_clears_cached_connection_and_db_file(self):
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config, client_class=SqliteResultListener)
        with sq:
            pass
        assert sq._conn is None
        assert sq._db_file is None

    def test_context_manager_allows_insert_and_select_by_row_name(self):
        config = FakeConfig(DB_FILE)
        sq = Sqliter(config=config, client_class=SqliteResultListener)
        with sq as conn:
            conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO t (id, name) VALUES (1, 'a')")
            conn.commit()
            row = conn.execute("SELECT * FROM t WHERE id = 1").fetchone()
            assert row["name"] == "a"


if __name__ == "__main__":
    unittest.main()
