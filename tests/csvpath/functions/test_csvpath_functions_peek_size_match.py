"""size() and peek_size() as bare match components.

PeekSize used to override matches() with self.matches = self.default_match().
That replaced the method with a bool and returned None, so a bare size("s")
did not match on the first line and raised TypeError ("'bool' object is not
callable") on the second. It now calculates its value, so argument errors
still surface, and takes the default match, like add() and divide().
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


@pytest.mark.parametrize("name", ["size", "peek_size"])
def test_bare_size_matches_every_line(name):
    path = CsvPath()
    path.parse(
        f"""~ validation-mode: raise, no-print ~ ${PATH}[1*][ push.nocontrib("s", 3) {name}("s") ]"""
    )
    lines = path.collect()
    assert len(lines) == 8


@pytest.mark.parametrize("name", ["size", "peek_size"])
def test_bare_size_with_another_component(name):
    #
    # size() contributes the default match, so the line matches when the
    # other component does
    #
    path = CsvPath()
    path.parse(
        f"""~ validation-mode: raise, no-print ~ ${PATH}[1*][ #lastname == "Bat" {name}("s") ]"""
    )
    lines = path.collect()
    assert len(lines) == 7


@pytest.mark.parametrize("name", ["size", "peek_size"])
def test_value_form_is_unchanged(name):
    path = CsvPath()
    path.parse(
        f"""~ validation-mode: raise, no-print ~ ${PATH}[1*][ push.nocontrib("s", 3) @r = {name}("s") ]"""
    )
    path.fast_forward()
    assert path.variables["r"] == 8
