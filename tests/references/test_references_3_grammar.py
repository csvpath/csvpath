import pytest
from lark import UnexpectedInput

from csvpath.references.reference_grammar_3 import QueryParser3


#
# grammar-level tests only. these confirm REFERENCE_GRAMMAR_3 accepts every
# example in "creating references v3.txt" and rejects the structural
# violations called out in that spec (empty root_major, "#" outside its one
# legal position, leading "/" in a path, etc).
#
# datatype-specific semantic rules -- e.g. name_three being required for
# files/csvpaths but optional for results -- are deliberately NOT enforced
# by the grammar (see reference_grammar_3.py's module docstring) and so are
# not tested here. those belong to the transformer/finder, not yet built.
#


POSITIVE_CASES = [
    # files
    '$*.files.Q2/test-data.:last()',
    '$acme.files.Q2/:name(*).:last()',
    '$acme.files.Q2/:name(@customer).:last()',
    '$acme.files.Q2/test-data.:last()',
    '$acme.files.:quarter()/:name("live data").:last()',
    '$acme.files.:date("2026-01-20").:to(:index(5))',
    '$acme.files.*.:last()',
    '$acme.files.:all().:first()',
    '$acme.files.*#my_worksheet.:type("xlsx")',
    '$acme.files.*#my_worksheet.:at(-1)',
    '$acme.files.*.:uuid("a4ff-82b9-...")',
    '$acme.files.*.:index(7)',
    '$acme.files.*.:from(:index(0)):to(@index)',
    '$acme.files.*.:last():before(:today())',
    '$*.files.*/more/pathnames.:last()',
    # csvpaths
    '$acme.csvpaths.:before(:yesterday()):after(:date("2024-08-01")):index(3).company-names',
    '$acme.csvpaths.:last().company_names',
    '$*.csvpaths.*.:uuid("a901-33b9-...")',
    '$acme.csvpaths.:uuid("a901-33b9-...").:index(3)',
    '$acme.csvpaths.:uuid("a901-33b9-...").:index(@which)',
    '$acme.csvpaths.:last().:all()',
    # results
    '$acme.results.:all()',
    '$acme.results.:last()',
    '$acme.results.customers/2025:first()',
    '$acme.results.customers/2025:first().invoices',
    '$acme.results.*/2025:first().invoices',
    '$acme.results.*/*/2025:first().invoices',
    '$acme.results.:name(^[^M].*)/2025:first().invoices',
    '$acme.results.:choice("acme|star|general")/2025:first().invoices',
    '$acme.results.:names(*)/2025:first().invoices:type("csv")',
    '$acme.results.:names(*)/2025:first().invoices:name("report.txt")',
    '$acme.results.customers/2025:first().invoices:data()',
    '$acme.results.customers/2025:first().invoices:vars()',
    '$acme.results.customers/2025:first().invoices:meta()',
    '$acme.results.customers/2025:first().:all():data()',
    '$acme.results.customers/2025:first().:from(2):unmatched()',
    '$acme.results.customers/:year():first().:from(2):unmatched()',
    '$acme.results.customers/:date("2025-01-01"):first().:from(2):unmatched()',
    '$acme.results.customers/:from(:date("2025-01-01")):first().:from(2):unmatched()',
    '$acme.results.customers/:from(:index(-1)).:from(2):unmatched()',
    '$acme.results.customers/:from(:index(-1)).*:type("parquet")',
    # % escaping / URL encoding (spec NOTES, not in the datatype example lists)
    '$acme.files.:name("100%%done").:data()',
    '$acme.files.:name("100%20done").:data()',
    '$acme.files.:name("say \\"hi\\"").:data()',
    # delimited regex literal (REGEX) -- for grouping/quotes BARE_ARG cannot represent
    '$acme.results.:name(/^[^M].*/)/2025:first().invoices',
    '$acme.results.:name(/^(?:Mon|Tue)day$/)/2025:first().invoices',
    '$acme.results.:name(/^(Mon|Tue)day$/)/2025:first().invoices',
    '$acme.results.:name(/contains"quote/)/2025:first().invoices',
]

NEGATIVE_CASES = [
    '$.files.:name("x").:data()',  # root_major cannot be empty
    '$*orders.files.:name("x").:data()',  # root_major cannot mix * and a name
    '$orders#sub.files.:name("x").:data()',  # root_minor ("#" at root) removed
    '$orders.files.:name("x").:data()#four',  # name_three cannot carry "#"
    '$*.files./Acme.:data()',  # leading "/" in a name_one path is illegal
    '$orders.csvpaths..',  # empty name_one is illegal
    '$acme.files.:name("x".:data()',  # unclosed function paren
    '$acme.files.:last.:data()',  # function missing parens entirely
    '$acme.files.:().:data()',  # empty function name
]


@pytest.fixture(scope="module")
def parser() -> QueryParser3:
    return QueryParser3()


@pytest.mark.parametrize("reference", POSITIVE_CASES)
def test_positive_case_parses(parser, reference):
    assert parser.validate_query(reference) is True


@pytest.mark.parametrize("reference", NEGATIVE_CASES)
def test_negative_case_is_rejected(parser, reference):
    assert parser.validate_query(reference) is False


def test_parse_returns_a_tree_for_valid_reference(parser):
    tree = parser.parse('$acme.files.*.:last()')
    assert tree is not None


def test_parse_raises_unexpected_input_for_invalid_reference(parser):
    with pytest.raises(UnexpectedInput):
        parser.parse('$.files.:name("x").:data()')


@pytest.mark.parametrize("bad_query", [None, ""])
def test_parse_raises_value_error_for_none_or_empty(parser, bad_query):
    with pytest.raises(ValueError):
        parser.parse(bad_query)
