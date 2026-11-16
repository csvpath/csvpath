import pytest

from csvpath.references.functions.filters.does_not_have_value_3 import DoesNotHaveValue3
from csvpath.references.functions.filters.has_value_3 import HasValue3
from csvpath.references.functions.filters.true_3 import True3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3

#
# RC triage B5 (David, 2026-11-16): a manifest-backed collection field
# takes only the two value predicates. An equality test on a list or a
# dict means nothing (compendium 6.40). The definition-backed collections
# (sources, destinations, webhooks*, scripts, transfers) still refuse an
# argument: their finders' gates read manifest fields only (decision D27).
#
COLLECTIONS = ["named_paths", "named_paths_identities", "file_fingerprints"]
DEFINITION_COLLECTIONS = ["sources", "destinations", "webhooks", "scripts", "transfers"]


def _build(name: str, arg):
    return ReferenceFunctionFactory.get_registered_class(name)(arg=arg)


@pytest.mark.parametrize("name", COLLECTIONS)
def test_a_collection_takes_a_value_predicate(name):
    _build(name, HasValue3()).check_valid()
    _build(name, DoesNotHaveValue3()).check_valid()
    _build(name, None).check_valid()


@pytest.mark.parametrize("name", COLLECTIONS)
@pytest.mark.parametrize("arg", ["x", 1])
def test_a_collection_rejects_an_equality_arg(name, arg):
    with pytest.raises(ReferenceException3):
        _build(name, arg).check_valid()


@pytest.mark.parametrize("name", COLLECTIONS)
def test_a_collection_rejects_another_predicate(name):
    with pytest.raises(ReferenceException3):
        _build(name, True3()).check_valid()


@pytest.mark.parametrize("name", DEFINITION_COLLECTIONS)
def test_a_definition_collection_still_refuses_an_arg(name):
    with pytest.raises(ReferenceException3):
        _build(name, HasValue3()).check_valid()
