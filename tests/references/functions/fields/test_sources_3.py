import pytest

from csvpath.references.functions.fields.sources_3 import Sources3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Sources3()
    assert f.name == "sources"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.FILES: "sources"}


def test_no_arg_is_valid():
    Sources3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Sources3(arg="x").check_valid()
