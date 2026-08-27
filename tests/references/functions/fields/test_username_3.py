import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.username_3 import Username3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Username3()
    assert f.name == "username"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "username"}
    assert f.LEDGER_KEY == {
        Reference3.FILES: "username",
        Reference3.CSVPATHS: "username",
    }


def test_no_arg_is_valid():
    Username3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Username3(arg="x").check_valid()
