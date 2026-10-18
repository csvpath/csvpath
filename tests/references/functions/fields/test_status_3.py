import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.status_3 import Status3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Status3()
    assert f.name == "status"
    assert f.ROLE == Function3.VALUE
    # widened 2026-10-18 to also cover FILES -- the global arrivals
    # ledger's own "status" field (a failure message), distinct from
    # RESULTS' own lifecycle marker, same literal key by coincidence.
    assert f.DATATYPES == (Reference3.RESULTS, Reference3.FILES)
    assert f.SOURCE == "manifest"
    # KEY has NO FILES entry -- status is genuinely ledger-only there
    # (never written to any per-name manifest), so it goes in
    # LEDGER_KEY instead, per username_3.py's own established
    # precedent.
    assert f.KEY == {
        Reference3.RESULTS: "status",
    }
    assert f.LEDGER_KEY == {
        Reference3.FILES: "status",
    }
    assert f.POSITIONS == {
        Reference3.RESULTS: (Reference3.NAME_ONE,),
        Reference3.FILES: (Reference3.NAME_ONE,),
    }


def test_no_arg_is_valid():
    Status3().check_valid()  # should not raise


class TestArgument:
    # ARG_TYPES widened 2026-10-18 from () -- FILES' own worked example
    # ("$*.files.:status(\"Registration failed\"):named_file_name(
    # \"orders\")") always carries a string argument. A side effect,
    # confirmed consistent with every other such widening this
    # session: RESULTS' own already-generic field_call/_matches_field_
    # predicate GATE mechanism picks this up for free too (e.g.
    # ":status(\"started\")" as a RESULTS GATE), not just FILES.
    def test_string_arg_is_valid(self):
        Status3(arg="Registration failed").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            Status3(arg=1).check_valid()
