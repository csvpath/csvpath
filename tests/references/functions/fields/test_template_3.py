import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.template_3 import Template3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Template3()
    assert f.name == "template"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.SOURCE == "manifest"
    assert f.BARE_SOURCE == "definition"
    assert f.KEY == {
        Reference3.FILES: "template",
        Reference3.CSVPATHS: "template",
        Reference3.RESULTS: "template",
    }
    assert f.LEDGER_KEY == {Reference3.RESULTS: "template"}


def test_no_arg_is_valid():
    Template3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Template3(arg="x").check_valid()
