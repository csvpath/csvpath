import pytest

from csvpath.references.functions.fields.transfers_3 import Transfers3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Transfers3()
    assert f.name == "transfers"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.CSVPATHS: "transfers.path_transfers"}


def test_no_arg_is_valid():
    Transfers3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Transfers3(arg="x").check_valid()
