import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_files_root_3 import NamedFilesRoot3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedFilesRoot3()
    assert f.name == "named_files_root"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {}
    assert f.LEDGER_KEY == {Reference3.RESULTS: "named_files_root"}


def test_no_arg_is_valid():
    NamedFilesRoot3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedFilesRoot3(arg="x").check_valid()
