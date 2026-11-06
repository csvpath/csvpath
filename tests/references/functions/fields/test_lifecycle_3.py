import pytest

from csvpath.managers.registrar import Registrar
from csvpath.references.functions.fields.lifecycle_3 import Lifecycle3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3

ALL = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)


def test_metadata():
    f = Lifecycle3()
    assert f.name == "lifecycle"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == ALL
    assert f.SOURCE == "manifest"
    assert ReferenceFunctionFactory.get_registered_class("lifecycle") is Lifecycle3


def test_it_is_ledger_only_in_every_datatype():
    # only the root ledgers hold a lifecycle (harmonization PR 6): no
    # per-name manifest, run manifest or instance manifest does
    f = Lifecycle3()
    assert f.KEY == {}
    assert f.LEDGER_KEY == {dt: "lifecycle" for dt in ALL}
    assert f.POSITIONS == {dt: (Reference3.NAME_ONE,) for dt in ALL}


def test_the_values_are_the_registrar_constants():
    # what the ledgers write, so what a gate argument matches
    assert (Registrar.ACTIVE, Registrar.DELETED) == ("active", "deleted")


def test_no_arg_is_the_field():
    Lifecycle3().check_valid()  # should not raise


@pytest.mark.parametrize("arg", ["active", "deleted"])
def test_a_string_arg_is_a_gate(arg):
    Lifecycle3(arg=arg).check_valid()  # should not raise


def test_a_non_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Lifecycle3(arg=1).check_valid()
