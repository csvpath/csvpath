import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.host_3 import Host3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Host3()
    assert f.name == "host"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {}
    assert f.LEDGER_KEY == {
        Reference3.FILES: "ip_address",
        Reference3.CSVPATHS: "ip_address",
    }


def test_no_arg_is_valid():
    Host3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Host3(arg="x").check_valid()
