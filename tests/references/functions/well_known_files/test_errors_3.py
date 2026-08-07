import pytest

from csvpath.references.functions.well_known_files.errors_3 import Errors3
from csvpath.references.functions.selectors.first_3 import First3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.idchain_3 import Idchain3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Errors3()
    assert f.name == "errors"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_no_arg_is_valid():
    Errors3().check_valid()  # should not raise


def test_plain_string_arg_is_rejected():
    # only a nested :idchain(...) call is a legal argument -- a bare
    # string is not (that would be ambiguous with an idchain value
    # written directly, which is not the syntax).
    with pytest.raises(ReferenceException3):
        Errors3(arg="x").check_valid()


def test_idchain_arg_is_accepted():
    Errors3(arg=Idchain3(arg="add[0]string[2]")).check_valid()  # should not raise


def test_a_different_functions_arg_is_rejected():
    # only Idchain3 specifically is meaningful here -- not just any
    # Function3.
    with pytest.raises(ReferenceException3):
        Errors3(arg=First3()).check_valid()
