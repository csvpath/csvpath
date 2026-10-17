import pytest

from csvpath.references.functions.fields.on_arrival_3 import OnArrival3
from csvpath.references.functions.filters.idchain_3 import Idchain3
from csvpath.references.functions.filters.not_none_3 import NotNone3
from csvpath.references.functions.well_known_files.definition_3 import Definition3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Definition3()
    assert f.name == "definition"
    # VALUE, not POINTER -- :definition() never narrows/selects
    # anything, even bare; same reasoning as Manifest3's own role fix
    # (this one was missed in that earlier pass).
    assert f.ROLE == Function3.VALUE
    # unlike Manifest3, results has no definition.json equivalent.
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)


def test_no_arg_is_valid():
    Definition3().check_valid()  # should not raise


def test_plain_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Definition3(arg="x").check_valid()


class TestPredicateArgumentFiltering:
    # ARG_TYPES widened 2026-10-17 to accept a nested Function3 -- the
    # generic predicate-argument filtering mechanism's own motivating
    # worked example: ":definition(:on_arrival(:not_none()))". check_valid()
    # cross-validates the nested call rather than relying on ARG_TYPES
    # alone (which only confirms "some Function3", not which one).
    def test_definition_sourced_field_accessor_with_predicate_is_valid(self):
        Definition3(arg=OnArrival3(arg=NotNone3())).check_valid()  # no raise

    def test_non_definition_sourced_field_accessor_is_rejected(self):
        # :idchain() has no SOURCE at all (None, not "definition") --
        # not a meaningful nested argument for :definition(), even
        # though it legitimately accepts a predicate argument itself
        # (confirming this raises because of Definition3's own SOURCE
        # check, not because the nested call rejects its own arg).
        with pytest.raises(ReferenceException3):
            Definition3(arg=Idchain3(arg=NotNone3())).check_valid()

    def test_definition_sourced_field_accessor_without_a_predicate_is_rejected(
        self,
    ):
        # :on_arrival() with no nested predicate at all -- not the
        # filtering shape; nothing else is supported as a nested
        # argument yet.
        with pytest.raises(ReferenceException3):
            Definition3(arg=OnArrival3()).check_valid()
