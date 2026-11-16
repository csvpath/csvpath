"""brief_stack_trace() is a side effect: it must not decide whether the line
matches. Its _decide_match never set self.match, so a bare
brief_stack_trace() made every line fail to match.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _count(body: str) -> int:
    path = CsvPath()
    path.parse(f"~ validation-mode: raise, no-print ~ ${PATH}[1*][ {body} ]")
    return len(path.collect())


@pytest.mark.parametrize("call", ['brief_stack_trace("log")', "brief_stack_trace()"])
def test_bare_brief_stack_trace_matches(call):
    assert _count(call) == 8


def test_the_other_components_decide():
    assert _count('#lastname == "Bat" brief_stack_trace("log")') == 7
    assert _count('no() brief_stack_trace("log")') == 0
