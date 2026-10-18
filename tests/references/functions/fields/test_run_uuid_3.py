import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.run_uuid_3 import RunUuid3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = RunUuid3()
    assert f.name == "run_uuid"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KIND == "uuid"
    assert f.KEY == {
        Reference3.RESULTS: "run_uuid",
        Reference3.RESULT: "run_uuid",
    }


def test_no_arg_is_valid():
    RunUuid3().check_valid()  # should not raise


def test_is_not_selector_when_argued():
    # distinct from :uuid() -- RunUuid3 has no FILES/CSVPATHS bare-
    # lookup shape at all (RESULTS-only), so there is no "entity" for
    # a bare form to select here; its argument is GATE-only.
    assert RunUuid3.SELECTOR_WHEN_ARGUED is False


class TestGateArgument:
    # ARG_TYPES widened 2026-10-18 from () -- normative_reference_
    # examples.txt's own worked examples ("$*.results.:manifest():
    # run_uuid(\"789a...\"):template()", "$*.results.:flatten():
    # run_uuid(\"789a...\"):template()") need a string argument to GATE
    # a pooled/manifest-read RESULTS candidate list by this field.
    def test_string_arg_is_valid(self):
        RunUuid3(arg="789a").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            RunUuid3(arg=1).check_valid()
