"""The examples in the format() and interpolate() descriptions work.

The format() description used to say to use ":.2f", which format()
rejects: it takes a format spec alone, with no leading colon. Only
interpolate() takes ":.2f", inside braces.
"""

import os
import pytest
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _run(match: str) -> CsvPath:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "collect")
    path.parse(f"${PATH}[1][ {match} ]")
    path.fast_forward()
    return path


@pytest.mark.parametrize(
    "match,expected",
    [
        ('@r = format(3.14159, ".2f")', "3.14"),
        ('@r = interpolate(3.14159, "{:.2f}")', "3.14"),
    ],
)
def test_documented_example(match, expected):
    path = _run(match)
    assert path.errors == []
    assert path.variables["r"] == expected


def test_a_leading_colon_in_format_is_an_error():
    path = _run('@r = format(3.14159, ":.2f")')
    assert path.variables.get("r") is None
    assert len(path.errors) == 1
    assert "Invalid format specifier" in path.errors[0].message


@pytest.mark.parametrize("name", ["format", "interpolate"])
def test_description_examples_match_the_code(name):
    # the description names the example that the tests above run
    path = _run(f'@r = {name}(3.14159, "{{:.2f}}")')
    f = path.matcher.expressions[0][0].children[0].right
    text = " ".join(f.description)
    if name == "format":
        assert 'format(3.14159, ".2f") gives "3.14"' in text
        assert ":.2f" not in text
    else:
        assert 'interpolate(3.14159, "{:.2f}") gives "3.14"' in text
        assert "{{" not in text
