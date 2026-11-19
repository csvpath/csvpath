"""Smoke test: every name registered in FunctionFactory parses and runs once.

Each name gets a minimal valid argument set, taken from its data and call
signatures in docs/func_gen/<name>.md. The test only checks that the csvpath
parses, that collect() runs without an exception, and that no error is
recorded. It does not check the values; the focused test files do that.

This catches registry regressions: a removed or renamed name, or a
check_valid() that rejects its own documented minimal arguments. Because
values are not checked, it does not catch an alias that points at the wrong
class. test_every_registered_name_is_covered fails when a new
name is registered without a row here.

Names that are skipped, and why:

- jev, noul, choice, score, criteria: the Jev family calls a remote model
  service. Never run here.
- import: needs a named-paths group in a CsvPaths run.
- jinja: needs named results in a CsvPaths run and a template; it is covered
  in tests/csvpaths/functions/test_csvpaths_functions_jinja.py.

PREVIOUSLY_UNTESTED lists the 16 names that no test used before this file
(specs/cvl_hardening/function_test_map.md). They are covered here.

Most rows run on every line of test.csv in collect mode. A few need their own
data file or an sqlite database; those are in SPECIAL.
"""

import os

import pytest
import sqlalchemy as sa

from csvpath import CsvPath
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.util.box import Box
from csvpath.util.printer import TestPrinter

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
LETTERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}lists{os.sep}letters.txt"
XSD_DIR = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_xsd{os.sep}"
JSON_DIR = (
    f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_jsonschema{os.sep}"
)

COLLECT = "~ validation-mode: collect, no-raise, no-print ~"

SKIPPED = {
    "jev": "calls a remote model service",
    "noul": "Jev family, calls a remote model service",
    "choice": "Jev family, calls a remote model service",
    "score": "Jev family, calls a remote model service",
    "criteria": "Jev family, calls a remote model service",
    "import": "needs a named-paths group in a CsvPaths run",
    "jinja": "needs named results in a CsvPaths run and a template",
}

PREVIOUSLY_UNTESTED = {
    "ge",
    "le",
    "equal",
    "not_equal_to",
    "inside",
    "outside",
    "range",
    "from_to",
    "before_after",
    "first_match",
    "first_scan",
    "unspecified",
    "when_do_stack",
    "size",
    "count_bytes",
    "fail_all",
}

# name -> the match part to run on test.csv[*]. Each row is the minimal valid
# call for that name. Setup such as a variable or a push goes before the call.
CALLS = {
    "above": "above(2, 1)",
    "add": "add(1, 2)",
    "advance": "advance(0)",
    "advance_all": "advance_all(0)",
    "after": "after(2, 1)",
    "after_blank": "after_blank()",
    "all": "all()",
    "alter": 'alter(#firstname, "a", "e")',
    "and": "and(yes(), yes())",
    "any": "any()",
    "append": 'append("x", "v")',
    "at_line": "at_line(1)",
    "average": 'average(1, "line")',
    "before": "before(1, 2)",
    "before_after": "before_after(5, 1, 3)",
    "below": "below(1, 2)",
    "between": "between(2, 1, 3)",
    "beyond": "beyond(5, 1, 3)",
    "blank": "line(string(#firstname), blank(#lastname), string(#say))",
    "boolean": "boolean(yes())",
    "brief_stack_trace": 'brief_stack_trace("log")',
    "caps": "caps(#firstname)",
    "clear": 'clear("s")',
    "collect": "collect(0)",
    "collect_original": "collect_original()",
    "concat": 'concat(#firstname, " ", #lastname)',
    "contains": 'contains(#say, "i")',
    "count": "count()",
    "count_bytes": "count_bytes()",
    "count_dups": "count_dups(#lastname)",
    "count_headers": "count_headers()",
    "count_headers_in_line": "count_headers_in_line()",
    "count_lines": "count_lines()",
    "count_scans": "count_scans()",
    "counter": "counter()",
    "datatype": "datatype(#firstname)",
    "date": 'date("2024-01-02")',
    "datetime": 'datetime("2024-01-02 10:11:12")',
    "day": 'day(date("2024-01-02"))',
    "debug": 'debug("error")',
    "decimal": '@n = "1.5" decimal(@n)',
    "divide": "divide(6, 3)",
    "do_when_stack": "do_when_stack()",
    "dup_lines": "dup_lines(#lastname)",
    "email": "email(#firstname)",
    "empty": "empty(#firstname)",
    "empty_stack": "empty_stack()",
    "end": "end()",
    "ends_with": 'ends_with(#firstname, "d")',
    "endswith": 'endswith(#firstname, "d")',
    "env": 'env("HOME")',
    "eq": "eq(1, 1)",
    "equal": "equal(1, 1)",
    "equals": "equals(1, 1)",
    "error": 'error("x")',
    "even": "@n = 2 even(@n)",
    "every": "every(#lastname, 2)",
    "exact": "exact(/hi!/, #say)",
    "exists": "exists(#firstname)",
    "fail": "fail()",
    "fail_all": "fail_all()",
    "fail_and_stop": "fail_and_stop(no())",
    "failed": "failed()",
    "false": "false()",
    "file_fingerprint": "file_fingerprint()",
    "find": 'find(#say, "i")',
    "fingerprint": "fingerprint()",
    "first": "first(#firstname)",
    "first_line": "first_line()",
    "first_match": "first_match()",
    "first_scan": "first_scan()",
    "firstline": "firstline()",
    "firstmatch": "firstmatch()",
    "firstscan": "firstscan()",
    "float": 'float("1.5")',
    "format": 'format(#firstname, ">10")',
    "format_date": 'format_date(date("2024-01-02"), "%Y")',
    "from_to": "from_to(2, 1, 3)",
    "ge": "ge(2, 1)",
    "get": 'get("x")',
    "gt": "gt(2, 1)",
    "gte": "gte(2, 1)",
    "has_dups": "has_dups(#lastname)",
    "has_matches": "has_matches()",
    "header_index": 'header_index("firstname")',
    "header_name": "header_name(0)",
    "header_names_match": 'header_names_match("firstname|lastname|say")',
    "header_names_mismatch": 'header_names_mismatch("firstname|lastname|say")',
    "header_table": "header_table()",
    "headers": "headers()",
    "headers_stack": "headers_stack()",
    "in": 'in(#firstname, "David|Fish")',
    "increment": "increment(yes(), 1)",
    "index_of": 'index_of("s", 1)',
    "insert": 'insert(1, "x", #say)',
    "inside": "inside(2, 1, 3)",
    "int": 'int("5")',
    "integer": '@n = "1" integer(@n)',
    "interpolate": 'interpolate(#firstname, "{:>10}")',
    "jsonpath": 'jsonpath("{\\"a\\": 1}", "$.a")',
    "last": "last()",
    "le": "le(1, 2)",
    "length": "length(#firstname)",
    "line": "line(string(#firstname), string(#lastname), string(#say))",
    "line_before": "line_before(#firstname)",
    "line_fingerprint": "line_fingerprint()",
    "line_number": "line_number()",
    "line_values_stack": "line_values_stack()",
    "log": 'log("x")',
    "lower": "lower(#firstname)",
    "lt": "lt(1, 2)",
    "lte": "lte(1, 2)",
    "matches": "matches()",
    "max": "max(1)",
    "max_length": "max_length(#firstname, 10)",
    "median": 'median(1, "line")',
    "metadata": "metadata()",
    "metaphone": "metaphone(#firstname)",
    "min": "min(1)",
    "min_length": "min_length(#firstname, 1)",
    "minus": "minus(3, 1)",
    "mismatch": "mismatch()",
    "missing": "missing()",
    "mod": "mod(5, 2)",
    "month": 'month(date("2024-01-02"))',
    "multiply": "multiply(2, 3)",
    "nand": "nand(yes(), no())",
    "neq": "neq(1, 2)",
    "no": "no()",
    "none": "none()",
    "nonspecific": "line(string(#firstname), nonspecific(#lastname), string(#say))",
    "nor": "nor(no(), no())",
    "not": "not(no())",
    "not_equal_to": "not_equal_to(1, 2)",
    "not_line": "not_line(1)",
    "now": "now()",
    "odd": "@n = 1 odd(@n)",
    "or": "or(yes(), no())",
    "outside": "outside(5, 1, 3)",
    "peek": 'peek("s", 0)',
    "peek_eq": 'peek_eq("s", 0, 1)',
    "peek_gt": 'peek_gt("s", 0, 1)',
    "peek_gte": 'peek_gte("s", 0, 1)',
    "peek_lt": 'peek_lt("s", 0, 1)',
    "peek_lte": 'peek_lte("s", 0, 1)',
    "peek_neq": 'peek_neq("s", 0, 1)',
    "peek_size": 'peek_size("s")',
    "percent": 'percent("line")',
    "percent_dups": "percent_dups(#lastname)",
    "percent_matching": "percent_matching()",
    "percent_unique": "percent_unique(#firstname)",
    "pop": 'pop("s")',
    "print": 'print("x")',
    "print_line": "print_line()",
    "print_queue": "print_queue()",
    "pstdev": 'pstdev("s")',
    "push": 'push("s", 1)',
    "push_distinct": 'push_distinct("s", 1)',
    "put": 'put("x", 1)',
    "random": "random(0, 1)",
    "range": "range(2, 1, 3)",
    "regex": "regex(/a/, #say)",
    "remove": "remove(2)",
    "rename": 'rename(2, "says")',
    "replace": 'replace(2, "x")',
    "reset_headers": "reset_headers()",
    "roll": 'roll(date("2024-01-02"), 1, "days")',
    "round": "round(1.234, 1)",
    "row_table": "row_table()",
    "run_table": "run_table()",
    "runtime": "runtime()",
    "shuffle": "shuffle(0, 10)",
    "size": 'size("s")',
    "skip": "skip(no())",
    "skip_all": "skip_all(no())",
    "slice": 'push("s", 1) slice("s", 0)',
    "sort": 'sort("s")',
    "stack": 'stack("s")',
    "starts_with": 'starts_with(#firstname, "D")',
    "startswith": 'startswith(#firstname, "D")',
    "stdev": 'stdev("s")',
    "stop": "stop(no())",
    "stop_all": "stop_all(no())",
    "store_line_fingerprint": "store_line_fingerprint()",
    "string": "string(#firstname)",
    "strip": "strip(#firstname)",
    "substring": "substring(#firstname, 2)",
    "subtotal": "@n = 1 subtotal(#lastname, @n)",
    "subtract": "subtract(3, 1)",
    "sum": "sum(1)",
    "take": "take(no())",
    "tally": "tally(#lastname)",
    "thismonth": "thismonth()",
    "thisyear": "thisyear()",
    "today": "today()",
    "too_long": "too_long(#firstname, 10)",
    "too_short": "too_short(#firstname, 1)",
    "total_lines": "total_lines()",
    "track": "track(#firstname, #lastname)",
    "track_any": "track_any(#firstname, #lastname)",
    "true": "true()",
    "unspecified": "line(string(#firstname), unspecified(#lastname), string(#say))",
    "upper": "upper(#firstname)",
    "url": "url(#firstname)",
    "uuid": "uuid()",
    "valid": "valid()",
    "validate": "validate()",
    "var_table": "var_table()",
    "variables": "variables()",
    "vote_stack": "vote_stack()",
    "when_do_stack": "when_do_stack()",
    "wildcard": "line(wildcard())",
    "xpath": 'xpath("<a>b</a>", "/a")',
    "year": 'year(date("2024-01-02"))',
    "yes": "yes()",
}

# error() records its own message as an error, by design
EXPECTED_ERRORS = {"error": ["x"]}

# names that need their own data file or a database. {db} is replaced with
# an sqlite connection string.
SPECIAL = {
    "load_list": (PATH, "*", f'load_list("{LETTERS}")'),
    "xsd": (f"{XSD_DIR}automobiles.xml", "0", f'xsd("{XSD_DIR}automobiles.xsd")'),
    "jsonschema": (
        f"{JSON_DIR}automobiles.json",
        "0",
        f'jsonschema("{JSON_DIR}automobiles.jsonschema")',
    ),
    "parquet": (
        PATH,
        "*",
        "parquet.smoke(string.firstname(#0), string.lastname(#1), string.say(#2))",
    ),
    "sql_in": (PATH, "*", 'sql_in("apple", "fruits", "name", "{db}")'),
    "select": (PATH, "*", 'select("name", "fruits", none(), "{db}")'),
}


@pytest.fixture(scope="module")
def sqlite_db(tmp_path_factory):
    """A local sqlite file with one table, for sql_in() and select()."""
    db_path = tmp_path_factory.mktemp("smoke") / "fruits.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE fruits (name TEXT NOT NULL)"))
        conn.execute(sa.text("INSERT INTO fruits (name) VALUES ('apple')"))
    engine.dispose()
    return f"sqlite:///{db_path}"


def _registered() -> list[str]:
    FunctionFactory.load()
    return sorted(FunctionFactory.MY_FUNCTIONS.keys())


def _run(*, file: str, scan: str, fragment: str) -> CsvPath:
    path = CsvPath()
    # keep print() and friends out of the test output
    path.set_printers([TestPrinter()])
    path.parse(f"{COLLECT} ${file}[{scan}][ {fragment} yes() ]")
    path.collect()
    return path


def _messages(*, path: CsvPath) -> list[str]:
    return [e.message for e in (path.errors or [])]


def test_every_registered_name_is_covered():
    # a new name must get a row here, or be skipped with a reason
    covered = set(CALLS) | set(SPECIAL) | set(SKIPPED)
    registered = set(_registered())
    assert registered - covered == set()
    # and no row may name a function that is not registered
    assert covered - registered == set()


def test_previously_untested_names_are_covered():
    assert PREVIOUSLY_UNTESTED <= set(CALLS)


@pytest.mark.parametrize("name", sorted(CALLS))
def test_name_parses_and_runs(name):
    path = _run(file=PATH, scan="*", fragment=CALLS[name])
    messages = _messages(path=path)
    if name in EXPECTED_ERRORS:
        # one message per line, all of them the expected one
        assert messages
        assert set(messages) == set(EXPECTED_ERRORS[name])
    else:
        assert messages == []


def _clear_sql_engine() -> None:
    # sql_in() and select() keep the first engine they create in the Box
    # and reuse it whatever connection string is given later. Without this
    # cleanup, later sql tests in the same process would query this test
    # database. See the PR body.
    box = Box()
    engine = box.get(key=Box.SQL_ENGINE)
    if engine is not None:
        engine.dispose()
        box.remove(Box.SQL_ENGINE)


@pytest.mark.parametrize("name", sorted(SPECIAL))
def test_special_name_parses_and_runs(name, sqlite_db):
    file, scan, fragment = SPECIAL[name]
    _clear_sql_engine()
    try:
        path = _run(file=file, scan=scan, fragment=fragment.replace("{db}", sqlite_db))
        assert _messages(path=path) == []
    finally:
        _clear_sql_engine()
