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


def test_str_arg_is_valid():
    # a named stream under print-mode:separate, added 2026-09-21 -- see
    # the normative doc's own ":printouts('greetings')" example.
    Printouts3(arg="greetings").check_valid()  # should not raise


def test_int_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Printouts3(arg=1).check_valid()
