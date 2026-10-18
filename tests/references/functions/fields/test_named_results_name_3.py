import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_results_name_3 import (
    NamedResultsName3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedResultsName3()
    assert f.name == "named_results_name"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "named_results_name",
        Reference3.RESULT: "named_results_name",
    }


def test_no_arg_is_valid():
    NamedResultsName3().check_valid()  # should not raise


class TestGateArgument:
    # ARG_TYPES widened 2026-10-18 from () -- compendium 6.7's "name"
    # functional group, same retrieve/select duality rule :uuid()
    # already has. A string argument GATES a pooled RESULTS candidate
    # list by this field.
    def test_string_arg_is_valid(self):
        NamedResultsName3(arg="widgets").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            NamedResultsName3(arg=1).check_valid()
