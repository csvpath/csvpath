import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.type_3 import Type3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Type3()
    assert f.name == "type"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.FILES: "type"}
    # POSITIONS widened 2026-10-18 to also include NAME_ONE -- the new
    # GATE position (e.g. ':type("csv")'), alongside its original,
    # unchanged NAME_THREE ordinary field-read position.
    assert f.POSITIONS == {
        Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)
    }


def test_no_arg_is_valid():
    Type3().check_valid()  # should not raise


class TestGateArgument:
    # ARG_TYPES widened 2026-10-18 from () -- compendium 3.9d's own
    # claimed equivalence (':type("csv")' == '*:type("csv")') plus its
    # own worked example (normative_reference_examples.txt line 271,
    # ':flatten():type("xlsx")') need a string argument to GATE a
    # candidate list in name_one. ':type()' is the sole member of
    # compendium 6.7's "type" functional group.
    def test_string_arg_is_valid(self):
        Type3(arg="csv").check_valid()  # should not raise

    def test_int_arg_is_rejected(self):
        with pytest.raises(ReferenceException3):
            Type3(arg=1).check_valid()
