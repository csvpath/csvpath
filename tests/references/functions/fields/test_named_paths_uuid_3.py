import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_uuid_3 import NamedPathsUuid3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPathsUuid3()
    assert f.name == "named_paths_uuid"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KIND == "uuid"
    assert f.KEY == {
        Reference3.RESULTS: "named_paths_uuid",
        Reference3.RESULT: "named_paths_uuid",
    }


def test_no_arg_is_valid():
    NamedPathsUuid3().check_valid()  # should not raise


class TestGateArgument:
    # ARG_TYPES widened 2026-10-18 from () -- compendium 6.7's "uuid"
    # functional group, same retrieve/select duality rule :uuid()/
    # :run_uuid() already have. A string argument GATES a pooled
    # RESULTS candidate list by this field.
    def test_string_arg_is_valid(self):
        NamedPathsUuid3(arg="45ad7aa7").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            NamedPathsUuid3(arg=1).check_valid()
