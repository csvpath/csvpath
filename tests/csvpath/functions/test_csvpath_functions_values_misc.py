"""One value-asserting test each for format/interpolate, metaphone, env, runtime, print_queue and run_table.

What the docs say (docs/func_gen/<name>.md, docs/functions/<name>.md):

- format(value, format) "Uses the Python string formatting mini language".
  interpolate(value, pattern) fills one {} replacement field in a complete
  formatting string.
- metaphone() gives a "sound-alike" phonetic transformation. The docs'
  example: "Sacks" and "Sax" get an identical transformation.
- env(name) reads the env var source. With [config] var_sub_source = env,
  that is the OS environment.
- runtime(name) gives the runtime indicators that go to meta.json, such as
  line_number and identity.
- print_queue() returns the number of strings sent to the printers so far.
- run_table() prints tables of the metadata and runtime names and values.

jinja() is not covered here because it needs a CsvPaths run and a template.

Not asserted, and reported in the PR body:

- the docs' format example, ":.2f", which gives None instead of "3.14"
- env() of a name that is not set, which returns the name, not None
"""

import os

import pytest

from csvpath import CsvPath
from csvpath.util.printer import TestPrinter

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _run(*, body: str, scan: str = "1", metadata: str = "") -> tuple[CsvPath, list]:
    path = CsvPath()
    printer = TestPrinter()
    path.set_printers([printer])
    path.parse(f"{metadata} ${PATH}[{scan}][ {body} ]")
    path.collect()
    return path, printer.lines


# ---------------------------------------------------------------------------
# format() and interpolate()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "call,expected",
    [
        ('format(3.14159, ".2f")', "3.14"),
        ('format(7, "03d")', "007"),
        ('format(#firstname, "0>8")', "000David"),
        ('interpolate(3.14159, "pi is {:.2f}")', "pi is 3.14"),
        ('interpolate(#firstname, "{}!")', "David!"),
    ],
)
def test_format_and_interpolate(call, expected):
    path, _ = _run(body=f"@result = {call}")
    assert path.variables["result"] == expected


# ---------------------------------------------------------------------------
# metaphone()
# ---------------------------------------------------------------------------


def test_metaphone_sound_alikes_match():
    path, _ = _run(body='@a = metaphone("Sacks") @b = metaphone("Sax")')
    # the docs: an identical transformation for "Sacks" and "Sax"
    assert path.variables["a"] == path.variables["b"]
    # the standard Metaphone code for both. The docs do not give the codes;
    # this pins the algorithm's output.
    assert path.variables["a"] == "SKS"


def test_metaphone_different_sounds_differ():
    path, _ = _run(body='@a = metaphone("Sacks") @b = metaphone(#firstname)')
    assert path.variables["a"] != path.variables["b"]


# ---------------------------------------------------------------------------
# env()
# ---------------------------------------------------------------------------


def test_env_reads_the_os_environment(monkeypatch):
    monkeypatch.setenv("CSVPATH_TEST_ENV_VALUE", "hello")
    path = CsvPath()
    # make the source the OS environment for this CsvPath, whatever the
    # config file says
    path.config.set(section="config", name="var_sub_source", value="env")
    path.parse(f'${PATH}[1][ @result = env("CSVPATH_TEST_ENV_VALUE") ]')
    path.collect()
    assert path.variables["result"] == "hello"


# ---------------------------------------------------------------------------
# runtime()
# ---------------------------------------------------------------------------


def test_runtime_line_number_per_line():
    path, _ = _run(body='push("lines", runtime("line_number"))', scan="1-3")
    assert path.variables["lines"] == [1, 2, 3]


def test_runtime_identity():
    path, _ = _run(body='@result = runtime("identity")', metadata="~ id: values ~")
    assert path.variables["result"] == "values"


# ---------------------------------------------------------------------------
# print_queue()
# ---------------------------------------------------------------------------


def test_print_queue_counts_printouts():
    # one print() per line, then the running count
    path, printed = _run(body='print("x") push("counts", print_queue())', scan="1-3")
    assert printed == ["x", "x", "x"]
    assert path.variables["counts"] == [1, 2, 3]


def test_print_queue_two_prints_on_a_line():
    path, printed = _run(body='print("one") print("two") @result = print_queue()')
    assert printed == ["one", "two"]
    assert path.variables["result"] == 2


# ---------------------------------------------------------------------------
# run_table()
# ---------------------------------------------------------------------------


def test_run_table_prints_the_metadata_and_runtime_tables():
    _, printed = _run(body="run_table()")
    # a heading, then a table, for each of the two sections
    assert printed[0] == "Metadata"
    assert printed[2] == "Runtime data"
    runtime_table = printed[3]
    # the docs: all the names and values available at each line
    for name in ("file_name", "total_lines", "line_number", "headers"):
        assert name in runtime_table
    assert "tests/csvpath/test_resources/test.csv".replace("/", os.sep) in (
        runtime_table
    )
