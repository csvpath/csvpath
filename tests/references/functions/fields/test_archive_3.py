import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.archive_3 import Archive3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Archive3()
    assert f.name == "archive"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.CSVPATHS: "archive_name",
        Reference3.RESULT: "archive_name",
    }
    assert f.LEDGER_KEY == {Reference3.RESULTS: "archive_name"}


def test_no_arg_is_valid():
    Archive3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Archive3(arg="x").check_valid()
