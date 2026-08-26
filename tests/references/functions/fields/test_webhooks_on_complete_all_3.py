import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.webhooks_on_complete_all_3 import (
    WebhooksOnCompleteAll3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = WebhooksOnCompleteAll3()
    assert f.name == "webhooks_on_complete_all"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.CSVPATHS: "webhooks.on_complete_all"}


def test_no_arg_is_valid():
    WebhooksOnCompleteAll3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        WebhooksOnCompleteAll3(arg="x").check_valid()
