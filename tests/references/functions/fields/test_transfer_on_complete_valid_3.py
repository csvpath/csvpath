import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.transfer_on_complete_valid_3 import (
    TransferOnCompleteValid3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = TransferOnCompleteValid3(arg="company_names")
    assert f.name == "transfer_on_complete_valid"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "definition"
    assert f.KEY == {
        Reference3.CSVPATHS: "transfers.path_transfers.{}.on_complete_valid"
    }


def test_string_arg_is_valid():
    TransferOnCompleteValid3(arg="company_names").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        TransferOnCompleteValid3().check_valid()


def test_non_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        TransferOnCompleteValid3(arg=10).check_valid()
