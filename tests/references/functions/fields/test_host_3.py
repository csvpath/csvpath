import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.host_3 import Host3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Host3()
    assert f.name == "host"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "hostname"}
    assert f.LEDGER_KEY == {
        Reference3.FILES: "hostname",
        Reference3.CSVPATHS: "hostname",
    }


def test_no_arg_is_valid():
    Host3().check_valid()  # should not raise


def test_a_string_arg_is_a_filter():
    # compendium 6.40: an argument to a field accessor filters (refused one
    # until 2026-11-15; RC triage A6/H)
    Host3(arg="x").check_valid()  # should not raise


def test_a_non_string_arg_raises():
    with pytest.raises(ReferenceException3):
        Host3(arg=5).check_valid()
