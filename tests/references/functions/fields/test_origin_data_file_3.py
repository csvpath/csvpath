import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.origin_data_file_3 import OriginDataFile3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = OriginDataFile3()
    assert f.name == "origin_data_file"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULT: "origin_data_file"}


def test_no_arg_is_valid():
    OriginDataFile3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        OriginDataFile3(arg="x").check_valid()
