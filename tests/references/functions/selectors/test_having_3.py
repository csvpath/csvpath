import pytest

from csvpath.references.functions.selectors.having_3 import Having3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Having3(arg="my_validations")
    assert f.name == "having"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.POSITIONS == {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }


def test_str_arg_is_valid():
    Having3(arg="x").check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Having3().check_valid()


def test_non_str_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Having3(arg=1).check_valid()
