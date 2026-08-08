import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.well_known_files.vars_3 import Vars3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Vars3()
    assert f.name == "vars"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_no_arg_is_valid():
    Vars3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Vars3(arg="x").check_valid()
