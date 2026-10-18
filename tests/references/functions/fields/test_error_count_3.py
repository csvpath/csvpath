import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.error_count_3 import ErrorCount3
from csvpath.references.functions.selectors.after_3 import After3
from csvpath.references.functions.selectors.before_3 import Before3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ErrorCount3()
    assert f.name == "error_count"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    # KEY widened 2026-10-18 to include Reference3.RESULT (instance
    # level) -- the per-instance "error_count" field was already being
    # written by result_registrar.py, this class just never exposed it.
    assert f.KEY == {
        Reference3.RESULTS: "error_count",
        Reference3.RESULT: "error_count",
    }
    assert f.POSITIONS == {
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }


def test_no_arg_is_valid():
    ErrorCount3().check_valid()  # should not raise


def test_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ErrorCount3(arg="x").check_valid()


class TestPredicateArgument:
    # ARG_TYPES widened 2026-10-18 from () -- normative_reference_
    # examples.txt's own worked examples need a predicate argument (or
    # a bare int, for an exact-match shorthand) to GATE a pooled '*'/
    # ':flatten()' candidate list by this field, not just read the
    # number off one already-selected entity.
    def test_above_predicate_is_valid(self):
        ErrorCount3(arg=After3(arg=3)).check_valid()  # should not raise

    def test_below_predicate_is_valid(self):
        ErrorCount3(arg=Before3(arg=1)).check_valid()  # should not raise

    def test_bare_int_exact_match_is_valid(self):
        ErrorCount3(arg=0).check_valid()  # should not raise
