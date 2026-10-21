import pytest

from csvpath.references.functions.selectors.choice_3 import ChoiceSelector3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ChoiceSelector3(arg="orders|invoices")
    assert f.name == "choice"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.POSITIONS == {
        Reference3.FILES: (Reference3.ROOT_MAJOR,),
        Reference3.CSVPATHS: (Reference3.ROOT_MAJOR,),
        Reference3.RESULTS: (Reference3.ROOT_MAJOR,),
    }


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ChoiceSelector3().check_valid()


def test_str_arg_is_valid():
    ChoiceSelector3(arg="orders|invoices").check_valid()  # should not raise


def test_non_str_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ChoiceSelector3(arg=5).check_valid()


class TestNames:
    def test_splits_on_pipe(self):
        assert ChoiceSelector3(arg="orders|invoices|shipments").names == [
            "orders",
            "invoices",
            "shipments",
        ]

    def test_trims_surrounding_whitespace(self):
        assert ChoiceSelector3(arg="orders | invoices |shipments").names == [
            "orders",
            "invoices",
            "shipments",
        ]

    def test_single_name_with_no_pipe(self):
        assert ChoiceSelector3(arg="orders").names == ["orders"]


class TestPattern:
    # compiles down to an anchored, escaped regex alternation -- the
    # whole point being that this is handed straight to the same
    # machinery :regex() already uses everywhere (_compile_path_
    # pattern, root_major dispatch, _is_traversal_root).
    def test_pattern_is_an_anchored_escaped_alternation(self):
        assert (
            ChoiceSelector3(arg="orders|invoices").pattern
            == "^(orders|invoices)$"
        )

    def test_pattern_matches_exactly_one_alternative(self):
        import re

        pattern = ChoiceSelector3(arg="orders|invoices").pattern
        assert re.search(pattern, "orders")
        assert re.search(pattern, "invoices")
        assert not re.search(pattern, "orders_extra")
        assert not re.search(pattern, "shipments")

    def test_special_regex_characters_in_a_name_are_escaped(self):
        # a named-file/named-paths/named-results name containing a
        # literal "." must only match that literal "." -- not "any
        # character", which is what an un-escaped regex would do.
        import re

        pattern = ChoiceSelector3(arg="a.b|c").pattern
        assert re.search(pattern, "a.b")
        assert not re.search(pattern, "axb")
