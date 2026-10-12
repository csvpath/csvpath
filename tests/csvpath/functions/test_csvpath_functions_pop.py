import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
FOOD = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}food.csv"


class TestCsvPathFunctionsPop(unittest.TestCase):
    def test_function_push1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push("pushed", count_lines())
                @popped = pop("pushed")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 0
        assert path.variables["popped"] == 9

    def test_function_push2(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                no()
                push.notnone("pushed", none())
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_push3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push.notnone("pushed", yes() )
                push("pushed2", yes() )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert "pushed" in path.variables
        assert len(path.variables["pushed"]) == 9

    def test_function_push4(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ test is a dupe from empty_stack. keeping in case the
              functions vary independently ~
            ${FOOD}[7*][
                push.skipnone("empties", empty_stack(#year, #healthy) )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 4
        assert "empties" in path.variables
        assert isinstance(path.variables["empties"], list)
        s = path.variables["empties"]
        assert len(s) == 1
        s2 = s[0]
        assert isinstance(s2, list)
        assert len(s2) == 1
        assert s2 == ["year"]

    def test_function_push5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("pushed", yes() )
                push( @pushed, yes() )
            ]"""
        )
        path.fast_forward()
        assert "pushed" in path.variables
        assert len(path.variables["pushed"]) == 2

    def test_function_push6(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                push("pushed")
            ]"""
        )
        path.fast_forward()
        assert "pushed" in path.variables
        assert path.variables["pushed"] == []

    def test_function_push7(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, no-print~
            ${PATH}[1*]
            [
                get("pushed")
                push("pushed")
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_peek(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push_distinct("pushed", #lastname )
                push.distinct("dis", #lastname )
                ~ who was second? ~
                @peek = peek("dis", 1)
                @peeksize = peek_size("dis")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 3
        assert len(path.variables["dis"]) == 3
        assert path.variables["peek"] == "Kermit"
        assert path.variables["peeksize"] == 3

    def test_function_pop1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push("pushed", count_lines())
                @popped = pop("pushed")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 0
        assert path.variables["popped"] == 9

    def test_function_stack1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @r = stack("st")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert path.variables["r"] == []

    def test_function_stack2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2+3]
            [
                push("st", #1)
                @r = stack("st")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["r"] == ["Bat", "Bat"]


#
# #357: pop() removed the top two items while returning the top one. The
# tests above only pop from a one-item stack, where that happens to be
# right. These pop from stacks of every size and check what remains.
#


def _run(body: str, *, scan: str = "[1]") -> CsvPath:
    path = CsvPath()
    path.parse(f"~ validation-mode: raise, no-print ~ ${PATH}{scan}[ {body} ]")
    path.fast_forward()
    return path


@pytest.mark.parametrize(
    "items,popped,remaining",
    [
        (["one"], "one", []),
        (["one", "two"], "two", ["one"]),
        (["one", "two", "three"], "three", ["one", "two"]),
        (["a", "b", "c", "d", "e"], "e", ["a", "b", "c", "d"]),
    ],
)
def test_function_pop_removes_one_item(items, popped, remaining) -> None:
    pushes = " ".join(f'push("s", "{i}")' for i in items)
    path = _run(f'{pushes} @top = pop("s")')
    assert path.variables["top"] == popped
    assert path.variables["s"] == remaining


def test_function_pop_until_empty() -> None:
    path = _run(
        'push("s", "one") push("s", "two") push("s", "three") '
        '@a = pop("s") @b = pop("s") @c = pop("s") @d = pop("s")'
    )
    assert path.variables["a"] == "three"
    assert path.variables["b"] == "two"
    assert path.variables["c"] == "one"
    #
    # popping an empty stack gives None and leaves it empty
    #
    assert path.variables["d"] is None
    assert path.variables["s"] == []


def test_function_pop_across_lines() -> None:
    #
    # two pushes and one pop per line: the stack grows by one each line
    #
    path = _run('push("s", line_number()) push("s", "x") @top = pop("s")', scan="[1-4]")
    assert path.variables["s"] == [1, 2, 3, 4]
    assert path.variables["top"] == "x"


def test_function_pop_then_peek() -> None:
    path = _run(
        'push("s", "one") push("s", "two") push("s", "three") '
        '@top = pop("s") @bottom = peek("s", 0) @size = peek_size("s")'
    )
    assert path.variables["top"] == "three"
    assert path.variables["bottom"] == "one"
    assert path.variables["size"] == 2


@pytest.mark.parametrize("value,matches", [("true", True), ("false", False)])
def test_function_pop_asbool(value: str, matches: bool) -> None:
    path = CsvPath()
    path.parse(
        f'~ validation-mode: raise, no-print ~ ${PATH}[1][ push("s", "keep") push("s", "{value}") pop.asbool("s") ]'
    )
    lines = path.collect()
    assert (len(lines) == 1) is matches
    assert path.variables["s"] == ["keep"]
