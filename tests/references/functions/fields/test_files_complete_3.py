import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.files_complete_3 import FilesComplete3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = FilesComplete3()
    assert f.name == "files_complete"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "all_expected_files",
        Reference3.RESULT: "files_expected",
    }


def test_no_arg_is_valid():
    FilesComplete3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        FilesComplete3(arg="x").check_valid()
