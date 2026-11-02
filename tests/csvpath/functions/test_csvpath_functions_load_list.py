"""load_list() outside a named-paths group run: the argument is the path of a
.txt file. tests/csvpaths/test_csvpaths_load_list.py covers group runs."""

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

LETTERS = "tests/csvpath/test_resources/lists/letters.txt"


@pytest.fixture
def data(tmp_path) -> str:
    p = tmp_path / "d.csv"
    p.write_text("id\na\nb\nc\nd\ne\n", encoding="utf-8")
    return str(p)


def _collect(data: str, body: str, *, validation: str | None = None):
    md = f"~ validation-mode: {validation} ~\n" if validation else ""
    path = CsvPath()
    lines = path.collect(f"{md}${data}[1*][ {body} ]")
    return path, [line[0] for line in lines]


def test_load_list_with_in(data: str) -> None:
    path, matched = _collect(data, f'@l = load_list("{LETTERS}") in(#id, @l)')
    #
    # blank lines skipped, values stripped
    #
    assert matched == ["b", "c", "d"]
    assert path.variables["l"] == ("b", "c", "d")


def test_load_list_directly_in_in(data: str) -> None:
    path, matched = _collect(data, f'in(#id, load_list("{LETTERS}"))')
    assert matched == ["b", "c", "d"]


def test_load_list_is_loaded_once_and_unchangeable(data: str) -> None:
    path, matched = _collect(data, f'@l = load_list("{LETTERS}") yes()')
    f = path.matcher.expressions[0][0].children[0].right
    assert f._values == ("b", "c", "d")
    assert isinstance(path.variables["l"], tuple)


def test_load_list_reads_the_file_once_when_the_run_starts(data: str, tmp_path) -> None:
    #
    # changing the file during the run changes nothing
    #
    p = tmp_path / "once.txt"
    p.write_text("a\ne\n", encoding="utf-8")
    path = CsvPath()
    path.parse(f'${data}[1*][ in(#id, load_list("{p}")) ]')
    matched = []
    for i, line in enumerate(path.next()):
        matched.append(line[0])
        if i == 0:
            p.write_text("b\n", encoding="utf-8")
    assert matched == ["a", "e"]


def test_load_list_empty_file(data: str, tmp_path) -> None:
    p = tmp_path / "empty.txt"
    p.write_text("\n\n", encoding="utf-8")
    path, matched = _collect(data, f'@l = load_list("{p}") in(#id, @l)')
    assert matched == []
    assert path.variables["l"] == ()


def test_load_list_unicode(data: str, tmp_path) -> None:
    p = tmp_path / "u.txt"
    p.write_text("é\nb\n", encoding="utf-8")
    path, matched = _collect(data, f'@l = load_list("{p}") in(#id, @l)')
    assert path.variables["l"] == ("é", "b")


@pytest.mark.parametrize(
    "arg",
    [
        "tests/csvpath/test_resources/lists/missing.txt",
        "tests/csvpath/test_resources/lists/letters",
        "tests/csvpath/test_resources/lists/letters.csv",
    ],
)
def test_load_list_cannot_load_raises(data: str, arg: str) -> None:
    with pytest.raises(MatchException):
        _collect(data, f'in(#id, load_list("{arg}"))')


def test_load_list_cannot_load_without_raise_is_invalid(data: str) -> None:
    #
    # even when errors don't raise, the run must not look clean
    #
    path, matched = _collect(
        data,
        'in(#id, load_list("tests/csvpath/test_resources/lists/missing.txt"))',
        validation="log, collect, no-raise",
    )
    assert matched == []
    assert path.is_valid is False
    assert path.stopped is True
    assert any("Cannot load list" in e.message for e in path.errors)


def test_load_list_needs_a_literal_name(data: str) -> None:
    #
    # the list is loaded at validation, so its name must be known then
    #
    with pytest.raises(Exception):
        _collect(data, '@n = "x" in(#id, load_list(@n))')
    with pytest.raises(Exception):
        _collect(data, "in(#id, load_list())")


def test_load_list_lists_tmp_as_a_value_qualifier(data: str) -> None:
    #
    # the generated function docs show value_qualifiers
    #
    path, matched = _collect(data, f'@l = load_list("{LETTERS}") yes()')
    f = path.matcher.expressions[0][0].children[0].right
    assert "tmp" in f.value_qualifiers
