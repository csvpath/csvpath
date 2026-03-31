import os
import pytest
import sqlalchemy as sa
from csvpath.matching.functions.sql.sql_in import SqlIn
from csvpath import CsvPath

TABLE = "fruits"
COLUMN = "name"
FRUITS = ["apple", "banana", "cherry", "date", "elderberry"]

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

@pytest.fixture(scope="module")
def engine():
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE TABLE {TABLE} ({COLUMN} TEXT NOT NULL)"))
        conn.execute(
            sa.text(f"INSERT INTO {TABLE} ({COLUMN}) VALUES (:val)"),
            [{"val": f} for f in FRUITS],
        )
    yield engine
    engine.dispose()

@pytest.fixture(scope="module")
def sqlite_fruits_db(tmp_path_factory):
    """Creates a populated SQLite file and returns its connection string.
    The file is cleaned up automatically after the module's tests finish."""
    db_path = tmp_path_factory.mktemp("data") / "fruits.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE TABLE {TABLE} ({COLUMN} TEXT NOT NULL)"))
        conn.execute(
            sa.text(f"INSERT INTO {TABLE} ({COLUMN}) VALUES (:val)"),
            [{"val": f} for f in FRUITS],
        )
    engine.dispose()
    yield f"sqlite:///{db_path}"
    # tmp_path_factory handles file deletion — nothing extra needed here



class TestCsvPathFunctionsSqlInFunction:
    def test_csvpath_sql_in_1(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""
            ~validation-mode:raise~
            ${PATH}[1][
                @apple = sql_in("apple", "fruits", "name", "{sqlite_fruits_db}", "true")
            ]
        """)
        print(f"vars: {path.variables}")
        assert "apple" in path.variables
        assert path.variables["apple"] is True

    def test_csvpath_sql_in_2(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""~validation-mode:raise~
                    ${PATH}[1][
                        @apple = sql_in("apple", "fruits", "name", "{sqlite_fruits_db}", "false")
                    ]""")
        print(f"vars: {path.variables}")
        assert "apple" in path.variables
        assert path.variables["apple"] is True

# --- no-cache tests ---

class TestCsvPathFunctionsSqlInLive:
    def test_csvpath_sql_in_value_present(self, engine):
        sql = SqlIn(None, "dummy")
        assert sql._do_query(engine=engine, table=TABLE, column=COLUMN, cache=False, value="apple") is True

    def test_csvpath_sql_in_value_absent(self, engine):
        sql = SqlIn(None, "dummy")
        assert sql._do_query(engine=engine, table=TABLE, column=COLUMN, cache=False, value="mango") is False

    def test_csvpath_sql_in_case_sensitive(self, engine):
        # SQLite TEXT is case-sensitive by default
        sql = SqlIn(None, "dummy")
        assert sql._do_query(engine=engine, table=TABLE, column=COLUMN, cache=False, value="Apple") is False

    def test_csvpath_sql_in_empty_string_absent(self, engine):
        sql = SqlIn(None, "dummy")
        assert sql._do_query(engine=engine, table=TABLE, column=COLUMN, cache=False, value="") is False

    def test_csvpath_sql_in_none_absent(self, engine):
        sql = SqlIn(None, "dummy")
        assert sql._do_query(engine=engine, table=TABLE, column=COLUMN, cache=False, value=None) is False

class TestCsvPathFunctionsSqlInLookup:
    def test_csvpath_sql_in_lookup_value_present(self, engine):
        sql = SqlIn(None, "dummy")
        assert sql._do_query(engine=engine, table=TABLE, column=COLUMN, cache=True, value="banana") is True

    def test_csvpath_sql_in_lookup_value_absent(self, engine):
        sql = SqlIn(None, "dummy")
        assert sql._do_query(engine=engine, table=TABLE, column=COLUMN, cache=True, value="mango") is False



