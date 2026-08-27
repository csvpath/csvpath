import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.archive_path_3 import ArchivePath3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ArchivePath3()
    assert f.name == "archive_path"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {}
    assert f.LEDGER_KEY == {Reference3.RESULTS: "archive_path"}


def test_no_arg_is_valid():
    ArchivePath3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ArchivePath3(arg="x").check_valid()
