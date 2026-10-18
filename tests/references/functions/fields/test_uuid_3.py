import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.uuid_3 import Uuid3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Uuid3()
    assert f.name == "uuid"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.SOURCE == "manifest"
    assert f.KIND == "uuid"
    assert f.KEY == {
        Reference3.FILES: "uuid",
        Reference3.CSVPATHS: "uuid",
        Reference3.RESULTS: "run_uuid",
        Reference3.RESULT: "uuid",
    }


def test_no_arg_is_valid():
    Uuid3().check_valid()  # should not raise


def test_is_selector_when_argued():
    # added 2026-10-18 -- the compendium's own stated rule for the
    # "uuid" functional group: "select an entity when its value
    # matches the function's argument." Same mechanism :fingerprint()
    # already has.
    assert Uuid3.SELECTOR_WHEN_ARGUED is True


class TestSelectByUuidArgument:
    # ARG_TYPES widened 2026-10-18 from () -- normative_reference_
    # examples.txt's own worked examples need a string argument to
    # SELECT an entity by known uuid (FILES/CSVPATHS, bare) or GATE a
    # pooled RESULTS candidate list (same mechanism :error_count()/
    # :named_file_name() use).
    def test_string_arg_is_valid(self):
        Uuid3(arg="ab37-fef3").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            Uuid3(arg=1).check_valid()
