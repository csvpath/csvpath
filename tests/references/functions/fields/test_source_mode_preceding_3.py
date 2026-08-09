import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.source_mode_preceding_3 import (
    SourceModePreceding3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = SourceModePreceding3()
    assert f.name == "source_mode_preceding"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULT: "source_mode_preceding"}


def test_no_arg_is_valid():
    SourceModePreceding3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        SourceModePreceding3(arg="x").check_valid()
