"""boolean(), date(), and datetime() accept an empty value unless notnone
(issue #300), as string(), integer(), decimal(), email(), url(), and uuid()
already did.

Each type gets one column, x, with three rows:

    1   a valid value for the type
    2   empty
    3   an invalid value
"""

import pytest

from csvpath import CsvPath

DATA = {
    "boolean": "id,x\n1,true\n2,\n3,perhaps\n",
    "date": "id,x\n1,2024-01-01\n2,\n3,nope\n",
    "datetime": "id,x\n1,2024-01-01 10:00:00\n2,\n3,nope\n",
}

#
# type -> the function call to test, with a format where the type takes one
#
CALLS = {
    "boolean": "{f}(#x)",
    "date": '{f}(#x, "%Y-%m-%d")',
    "datetime": '{f}(#x, "%Y-%m-%d %H:%M:%S")',
}


def _matched_ids(*, tmp_path, kind: str, expression: str) -> list[str]:
    data = tmp_path / f"{kind}.csv"
    data.write_text(DATA[kind], encoding="utf-8")
    path = CsvPath()
    lines = path.collect(
        f"~ validation-mode: print, no-raise ~ ${data}[1*][ {expression} ]"
    )
    return [line[0] for line in lines]


def _cases() -> list:
    cases = []
    for kind in DATA:
        plain = CALLS[kind].format(f=kind)
        notnone = CALLS[kind].format(f=f"{kind}.notnone")
        for expression, expected in [
            (plain, ["1", "2"]),
            (f"line( string(#id), {plain} )", ["1", "2"]),
            (f"or( no(), {plain} )", ["1", "2"]),
            #
            # the empty row matches the type function, so not() rejects it;
            # the invalid row 3 is rejected by its validation error
            #
            (f"not( {plain} )", []),
            (notnone, ["1"]),
            (f"line( string(#id), {notnone} )", ["1"]),
        ]:
            cases.append(
                pytest.param(kind, expression, expected, id=f"{kind}: {expression}")
            )
    return cases


@pytest.mark.parametrize("kind,expression,expected", _cases())
def test_validity_empty_type_values(
    tmp_path, kind: str, expression: str, expected: list
) -> None:
    ids = _matched_ids(tmp_path=tmp_path, kind=kind, expression=expression)
    assert ids == expected
