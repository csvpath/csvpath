import os
import pytest
import sqlalchemy as sa
from csvpath import CsvPath

TABLE = "fruits"
COLUMN = "name"
FRUITS = ["apple", "banana", "cherry", "date", "elderberry"]

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


@pytest.fixture(scope="module")
def sqlite_fruits_db(tmp_path_factory):
    """create a populated SQLite and return its connection string. clean up is automatic after tests finish."""
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


class TestCsvPathFunctionsSelectFunction:
    def test_csvpath_select_1(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""
            ~validation-mode:raise~
            ${PATH}[1][
                @fruits = select("name", "fruits", none(), "{sqlite_fruits_db}")
            ]
        """)
        print(f"vars: {path.variables}")
        assert "fruits" in path.variables
        assert isinstance(path.variables["fruits"], list)
        assert FRUITS == path.variables["fruits"]

    def test_csvpath_select_2(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""~validation-mode:raise~
                    ${PATH}[1][
                        push("faves", "apple", "date")
                        select.my_fruits("name", "fruits", "name='apple'", "{sqlite_fruits_db}")
                    ]""")
        print(f"vars: {path.variables}")
        assert "my_fruits" in path.variables
        assert isinstance(path.variables["my_fruits"], list)
        assert FRUITS != path.variables["my_fruits"]
        assert ["apple"] == path.variables["my_fruits"]

    def test_csvpath_select_3(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""~validation-mode:raise~
                    ${PATH}[1][
                        push("faves", "apple", "date")
                        select.my_fruits("name", "fruits", "name in @faves", "{sqlite_fruits_db}")
                    ]""")
        print(f"vars: {path.variables}")
        assert "my_fruits" in path.variables
        assert isinstance(path.variables["my_fruits"], list)
        assert FRUITS != path.variables["my_fruits"]
        assert path.variables.get("faves") == path.variables["my_fruits"]

    def test_csvpath_select_4(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""~validation-mode:raise~
                    ${PATH}[1][
                        push("faves", "apple", "date")
                        select.my_fruits("name", "fruits", "name in @faves and name != 'apple'", "{sqlite_fruits_db}")
                    ]""")
        print(f"vars: {path.variables}")
        assert "my_fruits" in path.variables
        assert isinstance(path.variables["my_fruits"], list)
        assert FRUITS != path.variables["my_fruits"]
        assert ["date"] == path.variables["my_fruits"]

    def test_csvpath_select_5(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""~validation-mode:raise~
                    ${PATH}[1][
                        push("faves", "apple", "date")
                        @not_fig = select.my_fruits("name", "fruits", "name in @faves and name != 'apple'", "{sqlite_fruits_db}")
                    ]""")
        print(f"vars: {path.variables}")
        assert "my_fruits" in path.variables
        assert isinstance(path.variables["my_fruits"], list)
        assert FRUITS != path.variables["my_fruits"]
        assert ["date"] == path.variables["my_fruits"]
        assert "not_fig" in path.variables
        assert ["date"] == path.variables.get("not_fig")

    def test_csvpath_select_6(self, sqlite_fruits_db):
        print(f"sqlite_fruits_db: {sqlite_fruits_db}")
        path = CsvPath()
        path.fast_forward(f"""~validation-mode:raise~
                    ${PATH}[*][
                        @line = line_number()
                        @line2 = line_number()
                        ~ line is created as a stack each iteration ~
                        @line = select("name", "fruits", "name = 'apple'", "{sqlite_fruits_db}")
                        ~ line2 is created as a stack once, then replaced with the line number ~
                        select.line2("name", "fruits", "name = 'apple'", "{sqlite_fruits_db}")
                    ]""")
        print(f"vars: {path.variables}")
        assert "line" in path.variables
        assert "line2" in path.variables
        assert isinstance(path.variables["line"], list)
        assert isinstance(path.variables["line2"], int)
