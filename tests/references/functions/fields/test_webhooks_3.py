import pytest

from csvpath.references.functions.fields.webhooks_3 import Webhooks3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Webhooks3()
    assert f.name == "webhooks"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.CSVPATHS: "webhooks"}


def test_no_arg_is_valid():
    Webhooks3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Webhooks3(arg="x").check_valid()
