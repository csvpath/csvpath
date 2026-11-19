"""
idchains, ExpressionUtility.my_chain. the top named component of an
expression carries the expression's index; each component below it
carries its position among its parent's children. Equality and Expression
are left out. see #770: two components with one chain made the second
one's error look like a duplicate, and it was dropped.
"""

import os
import pytest
from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility as exut

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _chains_of(*, match: str, name: str) -> list:
    """the chains of every component called name, in document order"""
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "collect")
    path.parse(f"${PATH}[1][ {match} ]")
    path.fast_forward()
    found = []

    def walk(t):
        if getattr(t, "name", None) == name and type(t).__name__ != "Term":
            found.append(exut.my_chain(t))
        for c in t.children:
            walk(c)

    for e in path.matcher.expressions:
        walk(e[0])
    return found


@pytest.mark.parametrize(
    "match,name,expected",
    [
        # top level, no Equality: already right before #770
        ('add("five", 1) add("five", 1)', "add", ["add[0]", "add[1]"]),
        # under an assignment: was add[1] for both
        ('@r = add("five", 1) @s = add("five", 1)', "add", ["add[0]", "add[1]"]),
        # left of a ==: was add[0] for both
        ('add("five", 1) == 3  add("five", 1) == 3', "add", ["add[0]", "add[1]"]),
        # under an assignment, in a later expression: was add[1]
        ('yes() yes() @r = add("five", 1)', "add", ["add[2]"]),
        # the nots were already right; the adds under them were not
        (
            'or(not(add("five", 1)), not(add("five", 1)))',
            "not",
            ["or[0].not[0]", "or[0].not[1]"],
        ),
        # below the top, position not expression index: was
        # or[0].not[0].add[0] twice
        (
            'or(not(add("five", 1)), not(add("five", 1)))',
            "add",
            ["or[0].not[0].add[0]", "or[0].not[1].add[0]"],
        ),
        # inner not is child 0 of the outer not: was not[1].not[1]
        ('yes() not(not(add("five", 1)))', "add", ["not[1].not[0].add[0]"]),
        # an Equality inside a function: add is position 1 of the ==
        ('yes() not(@a == add("five", 1))', "add", ["not[1].add[1]"]),
        # top named component under an assignment, child below it
        (
            '@r = not(add("five", 1)) @s = not(add("five", 1))',
            "add",
            ["not[0].add[0]", "not[1].add[0]"],
        ),
    ],
)
def test_idchain(match, name, expected):
    assert _chains_of(match=match, name=name) == expected


def test_idchain_unchanged_deep_chain():
    # the shape pinned in test_csvpath_expression_util.py
    assert _chains_of(match='any(length(concat("a", "b")))', name="concat") == [
        "any[0].length[0].concat[0]"
    ]


def test_idchains_are_unique_per_component():
    match = (
        '@r = add("five", 1) @s = add("five", 1) '
        'or(not(add("five", 1)), not(add("five", 1))) '
        'add("five", 1) == 3'
    )
    chains = _chains_of(match=match, name="add")
    assert len(chains) == 5
    assert len(set(chains)) == 5


@pytest.mark.parametrize(
    "match",
    [
        '@r = add("five", 1) @s = add("five", 1)',
        'add("five", 1) == 3  add("five", 1) == 3',
    ],
)
def test_same_error_from_two_components_collects_twice(match):
    # #770: the second add's error was dropped as a duplicate of the first,
    # then its calculation ran and left an unrelated "can only concatenate"
    # error in its place
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "collect")
    path.parse(f"${PATH}[1][ {match} ]")
    path.fast_forward()
    assert [e.source for e in path.errors] == ["add[0]", "add[1]"]
    msgs = [e.message for e in path.errors]
    assert msgs[0] == msgs[1]
    assert msgs[0].startswith("add requires one of")
