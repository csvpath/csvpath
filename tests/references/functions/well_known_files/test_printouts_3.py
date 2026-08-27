import pytest

from csvpath.references.functions.well_known_files.printouts_3 import Printouts3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Printouts3()
    assert f.name == "printouts"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_no_arg_is_valid():
    Printouts3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Printouts3(arg="x").check_valid()
