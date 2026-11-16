import pytest

from csvpath.references.function_describer_3 import Function3Describer
from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.functions.fields.files_complete_3 import FilesComplete3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = FilesComplete3()
    assert f.name == "files_complete"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "all_expected_files",
        Reference3.RESULT: "files_expected",
    }


def test_no_arg_is_valid():
    FilesComplete3().check_valid()  # should not raise


def test_a_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        FilesComplete3(arg="x").check_valid()


#
# disabled 2026-11-15 (David, RC triage B3): the class stays, unregistered
#
def test_it_is_not_registered():
    assert "files_complete" not in ReferenceFunctionFactory.registered_names()
    assert ReferenceFunctionFactory.get_registered_class("files_complete") is None


def test_it_is_not_described():
    assert ":files_complete()" not in Function3Describer.describe_all()
