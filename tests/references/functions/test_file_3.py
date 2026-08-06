import pytest

from csvpath.references.functions.file_3 import File3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = File3(arg="orders.parquet")
    assert f.name == "file"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_required_arg_present_and_correct_type_passes():
    File3(arg="orders.parquet").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        File3().check_valid()


def test_wrong_arg_type_is_rejected():
    with pytest.raises(ReferenceException3):
        File3(arg=5).check_valid()


class TestPathTraversalGuard:
    def test_forward_slash_is_rejected(self):
        with pytest.raises(ReferenceException3):
            File3(arg="sub/orders.parquet").check_valid()

    def test_backslash_is_rejected(self):
        with pytest.raises(ReferenceException3):
            File3(arg="sub\\orders.parquet").check_valid()

    def test_parent_traversal_is_rejected(self):
        with pytest.raises(ReferenceException3):
            File3(arg="../orders.parquet").check_valid()

    def test_bare_filename_is_accepted(self):
        File3(arg="orders.parquet").check_valid()  # should not raise
