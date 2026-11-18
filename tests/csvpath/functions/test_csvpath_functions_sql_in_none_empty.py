"""sql_in() with a None value and with an empty result, against local sqlite files only.

What the docs say (docs/func_gen/sql_in.md and sql_in's check_valid()):

- sql_in(value, table, column, connect string, [cache]) "Checks if a header
  value is present in a set of values found in a database. The functionality
  is similar to in()."
- The value may be None or the empty string (the data signature).
- With cache True, all the column's values are read once and looked up in
  memory; otherwise each line runs a query. Both must give the same answer.

Three databases, each with a fruits(name) table:

- full: apple, banana
- empty: no rows
- nulls: apple and a NULL

Each test clears the shared sql engine before and after it runs.
sql_in() reuses the first engine it creates whatever connection string it
is given later, which is reported in PR #749. Without the cleanup the tests
would query each other's databases.
"""

import os

import pytest
import sqlalchemy as sa

from csvpath import CsvPath
from csvpath.util.box import Box

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

COLLECT = "~ validation-mode: collect, no-raise, no-print ~"

DATABASES = {
    "full": ["apple", "banana"],
    "empty": [],
    "nulls": ["apple", None],
}


def _clear_sql_engine() -> None:
    box = Box()
    engine = box.get(key=Box.SQL_ENGINE)
    if engine is not None:
        engine.dispose()
        box.remove(Box.SQL_ENGINE)


@pytest.fixture(scope="module")
def databases(tmp_path_factory) -> dict[str, str]:
    """Creates the three sqlite files and returns their connection strings."""
    root = tmp_path_factory.mktemp("sql_in")
    connections = {}
    for name, values in DATABASES.items():
        engine = sa.create_engine(f"sqlite:///{root / name}.db")
        with engine.begin() as conn:
            conn.execute(sa.text("CREATE TABLE fruits (name TEXT)"))
            for value in values:
                conn.execute(sa.text("INSERT INTO fruits VALUES (:v)"), {"v": value})
        engine.dispose()
        connections[name] = f"sqlite:///{root / name}.db"
    return connections


@pytest.fixture(autouse=True)
def fresh_engine():
    _clear_sql_engine()
    yield
    _clear_sql_engine()


def _sql_in(*, value: str, conn: str, cache: str) -> tuple[object, list, list]:
    """Assigns sql_in() to @result on line 1. Returns @result, the lines and the errors."""
    path = CsvPath()
    path.parse(
        f"""{COLLECT} ${PATH}[1][
            @result = sql_in({value}, "fruits", "name", "{conn}", "{cache}")
        ]"""
    )
    lines = path.collect()
    return path.variables.get("result"), lines, [e.message for e in path.errors]


CACHE = ["true", "false"]


@pytest.mark.parametrize("cache", CACHE)
@pytest.mark.parametrize(
    "value,expected",
    [
        # the baseline: a present and an absent value
        ('"apple"', True),
        ('"kiwi"', False),
        # None and the empty string are allowed by the data signature, and
        # neither is in a table that has no NULL and no empty string
        ("none()", False),
        ('""', False),
    ],
)
def test_full_table(databases, cache, value, expected):
    result, _, errors = _sql_in(value=value, conn=databases["full"], cache=cache)
    assert errors == []
    assert result is expected


@pytest.mark.parametrize("cache", CACHE)
@pytest.mark.parametrize("value", ['"apple"', "none()", '""'])
def test_empty_result(databases, cache, value):
    # a table with no rows contains nothing, so every lookup is False,
    # with no error
    result, _, errors = _sql_in(value=value, conn=databases["empty"], cache=cache)
    assert errors == []
    assert result is False


@pytest.mark.parametrize("cache", CACHE)
def test_none_with_a_null_row(databases, cache):
    # pinned: the docs do not say whether None matches a NULL. Both modes
    # find it (the query compares with IS NULL; the cache holds None), so
    # the two modes agree.
    result, _, errors = _sql_in(value="none()", conn=databases["nulls"], cache=cache)
    assert errors == []
    assert result is True


@pytest.mark.parametrize("cache", CACHE)
def test_empty_string_with_a_null_row(databases, cache):
    # an empty string is not NULL
    result, _, errors = _sql_in(value='""', conn=databases["nulls"], cache=cache)
    assert errors == []
    assert result is False


@pytest.mark.parametrize("cache", CACHE)
def test_empty_result_fails_the_line(databases, cache):
    # like in(), sql_in() as a match component decides the match
    path = CsvPath()
    path.parse(
        f"""{COLLECT} ${PATH}[1][
            sql_in("apple", "fruits", "name", "{databases["empty"]}", "{cache}")
        ]"""
    )
    assert path.collect() == []
    assert path.errors == []
