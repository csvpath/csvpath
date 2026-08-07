import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.idchain_3 import Idchain3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Idchain3(arg="add[0]string[2]")
    assert f.name == "idchain"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_required_arg_present_and_correct_type_passes():
    Idchain3(arg="add[0]string[2]").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Idchain3().check_valid()


def test_wrong_arg_type_is_rejected():
    with pytest.raises(ReferenceException3):
        Idchain3(arg=5).check_valid()
