import os
import sys

import pytest

from csvpath import CsvPath
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.matching.functions.internal_functions import (
    InternalFunctions,
    InternalFunctionException,
)

PATH = os.path.join("tests", "csvpath", "test_resources", "test.csv")
IMPORTS = os.path.join("tests", "csvpath", "test_resources", "function.imports")
SAMPLE = "tests.csvpath.test_resources.internal_functions.sample_internal_function"
SAMPLE_LINE = f"from {SAMPLE} import SampleInternal as sample_internal\n"


@pytest.fixture
def internal(tmp_path, monkeypatch):
    """points InternalFunctions at a test imports file and starts it fresh.
    returns a function that writes the file's lines."""
    path = tmp_path / "internal.imports"
    path.write_text("", encoding="utf-8")
    monkeypatch.setattr(InternalFunctions, "IMPORTS", str(path))
    InternalFunctions.reset()
    sys.modules.pop(SAMPLE, None)

    def write(*lines: str) -> str:
        path.write_text("".join(lines), encoding="utf-8")
        return str(path)

    yield write
    InternalFunctions.reset()


def _builtins() -> dict:
    if len(FunctionFactory.MY_FUNCTIONS) == 0:
        FunctionFactory.load()
    return FunctionFactory.MY_FUNCTIONS


def test_internal_functions_shipped_file_reads_cleanly() -> None:
    #
    # the real internal.imports, next to FunctionFactory
    #
    assert os.path.exists(InternalFunctions.IMPORTS)
    table = InternalFunctions.read(path=InternalFunctions.IMPORTS, builtins=_builtins())
    assert isinstance(table, dict)


def test_internal_functions_read_parses_lines(internal) -> None:
    path = internal(
        "# a comment\n",
        "\n",
        SAMPLE_LINE,
        "  from a.b import C as d_e  \n",
    )
    table = InternalFunctions.read(path=path, builtins=_builtins())
    assert table == {
        "sample_internal": (SAMPLE, "SampleInternal"),
        "d_e": ("a.b", "C"),
    }


def test_internal_functions_read_imports_nothing(internal) -> None:
    path = internal(SAMPLE_LINE)
    InternalFunctions.read(path=path, builtins=_builtins())
    assert SAMPLE not in sys.modules


@pytest.mark.parametrize(
    "line",
    [
        "import a.b\n",
        "from a.b import C\n",
        "from a.b import C as\n",
        "from a.b import C as d extra\n",
        "from a.b include C as d\n",
        "from a.b import C like d\n",
    ],
)
def test_internal_functions_read_rejects_bad_lines(internal, line: str) -> None:
    path = internal(line)
    with pytest.raises(InternalFunctionException):
        InternalFunctions.read(path=path, builtins=_builtins())


@pytest.mark.parametrize("name", ["1abc", "a-b", "a.b", "_a"])
def test_internal_functions_read_rejects_bad_names(internal, name: str) -> None:
    path = internal(f"from a.b import C as {name}\n")
    with pytest.raises(InternalFunctionException):
        InternalFunctions.read(path=path, builtins=_builtins())


def test_internal_functions_read_rejects_duplicates(internal) -> None:
    path = internal(SAMPLE_LINE, "from a.b import C as sample_internal\n")
    with pytest.raises(InternalFunctionException):
        InternalFunctions.read(path=path, builtins=_builtins())


def test_internal_functions_read_rejects_builtin_names(internal) -> None:
    path = internal("from a.b import C as count\n")
    with pytest.raises(InternalFunctionException):
        InternalFunctions.read(path=path, builtins=_builtins())


def test_internal_functions_read_bad_input() -> None:
    with pytest.raises(ValueError):
        InternalFunctions.read(path="", builtins={})
    with pytest.raises(ValueError):
        InternalFunctions.read(path=None, builtins={})
    with pytest.raises(TypeError):
        InternalFunctions.read(path="x", builtins=None)
    with pytest.raises(FileNotFoundError):
        InternalFunctions.read(path="no/such/internal.imports", builtins={})


def test_internal_functions_unknown_name_is_none(internal) -> None:
    internal(SAMPLE_LINE)
    f = InternalFunctions.get_function(
        matcher=None, name="not_internal", builtins=_builtins()
    )
    assert f is None
    assert SAMPLE not in sys.modules


def test_internal_functions_get_function_imports_on_first_use(internal) -> None:
    internal(SAMPLE_LINE)
    f = InternalFunctions.get_function(
        matcher=None, name="sample_internal", builtins=_builtins()
    )
    assert SAMPLE in sys.modules
    assert type(f).__name__ == "SampleInternal"
    assert f.name == "sample_internal"


def test_internal_functions_class_is_cached(internal) -> None:
    internal(SAMPLE_LINE)
    InternalFunctions.get_function(
        matcher=None, name="sample_internal", builtins=_builtins()
    )
    first = InternalFunctions.function_class(name="sample_internal")
    #
    # once cached, a second lookup does not re-import the module
    #
    sys.modules.pop(SAMPLE, None)
    assert InternalFunctions.function_class(name="sample_internal") is first
    assert SAMPLE not in sys.modules


def test_internal_functions_file_is_read_once(internal) -> None:
    path = internal(SAMPLE_LINE)
    InternalFunctions.get_function(matcher=None, name="x", builtins=_builtins())
    os.remove(path)
    assert (
        InternalFunctions.get_function(
            matcher=None, name="sample_internal", builtins=_builtins()
        )
        is not None
    )


def test_internal_functions_missing_module(internal) -> None:
    internal("from csvpath.no_such_module import X as missing_internal\n")
    with pytest.raises(InternalFunctionException):
        InternalFunctions.get_function(
            matcher=None, name="missing_internal", builtins=_builtins()
        )


def test_internal_functions_missing_class(internal) -> None:
    internal(f"from {SAMPLE} import NoSuchClass as missing_internal\n")
    with pytest.raises(InternalFunctionException):
        InternalFunctions.get_function(
            matcher=None, name="missing_internal", builtins=_builtins()
        )


def test_internal_functions_class_must_be_a_function(internal) -> None:
    internal(f"from {SAMPLE} import NotAFunction as not_a_function\n")
    with pytest.raises(InternalFunctionException):
        InternalFunctions.get_function(
            matcher=None, name="not_a_function", builtins=_builtins()
        )
    assert "not_a_function" not in InternalFunctions._CLASSES


def test_internal_functions_function_class_unknown_name(internal) -> None:
    internal(SAMPLE_LINE)
    with pytest.raises(ValueError):
        InternalFunctions.function_class(name="sample_internal")
    InternalFunctions.get_function(matcher=None, name="x", builtins=_builtins())
    with pytest.raises(ValueError):
        InternalFunctions.function_class(name="not_internal")


def test_internal_functions_get_function_bad_input(internal) -> None:
    with pytest.raises(ValueError):
        InternalFunctions.get_function(matcher=None, name="", builtins={})
    with pytest.raises(ValueError):
        InternalFunctions.get_function(matcher=None, name=None, builtins={})
    with pytest.raises(TypeError):
        InternalFunctions.get_function(matcher=None, name="x", builtins=None)


#
# through FunctionFactory and a real run
#


def test_internal_functions_found_by_function_factory(internal) -> None:
    internal(SAMPLE_LINE)
    f = FunctionFactory.get_function(
        None, name="sample_internal", find_external_functions=False
    )
    assert type(f).__name__ == "SampleInternal"
    #
    # qualifiers work as they do for a built-in
    #
    f = FunctionFactory.get_function(
        None, name="sample_internal.onmatch", find_external_functions=False
    )
    assert f.onmatch is True


def test_internal_functions_builtins_still_load_first(internal) -> None:
    internal(SAMPLE_LINE)
    f = FunctionFactory.get_function(None, name="count", find_external_functions=False)
    assert type(f).__name__ == "Count"
    assert SAMPLE not in sys.modules


def test_internal_functions_unknown_name_still_fails(internal) -> None:
    internal(SAMPLE_LINE)
    assert (
        FunctionFactory.get_function(
            None, name="no_such_function", find_external_functions=False
        )
        is None
    )


def test_internal_functions_in_a_run(internal) -> None:
    internal(SAMPLE_LINE)
    path = CsvPath()
    path.fast_forward(f"${PATH}[*][ @a = sample_internal() ]")
    assert path.variables["a"] is True
    assert SAMPLE in sys.modules


def test_internal_functions_run_without_them_imports_nothing(internal) -> None:
    internal(SAMPLE_LINE)
    path = CsvPath()
    path.fast_forward(f"${PATH}[*][ @a = yes() ]")
    assert path.variables["a"] is True
    assert SAMPLE not in sys.modules


def test_internal_functions_externals_take_priority(internal) -> None:
    #
    # function.imports maps "sure" to Yes. an internal "sure" is never used.
    #
    internal(f"from {SAMPLE} import SampleInternal as sure\n")
    path = CsvPath()
    path.config.set(section="functions", name="imports", value=IMPORTS)
    path.fast_forward(f"${PATH}[*][ @a = sure() ]")
    assert path.variables["a"] is True
    assert SAMPLE not in sys.modules
