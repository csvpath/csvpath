import pytest

from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3

#
# csvpaths is required (no default) on ReferenceParser3 -- these tests
# do not exercise any csvpaths behavior, so a plain sentinel stands in
# for a real CsvPaths context throughout.
#
CSVPATHS = object()

#
# every positive example from "creating references v3.txt" / the grammar
# test corpus (test_references_3_grammar.py), run through the full
# string -> Reference3 -> ref_string round trip. these are the same
# strings the grammar already validated at the syntax level; here we
# confirm the transformer builds something and that rendering it back
# out reproduces the original exactly.
#
SPEC_EXAMPLES = [
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
    '$acme.csvpaths.:before(:yesterday()):after(:date("2024-08-01")):index(3).company-names',
    '$acme.csvpaths.:last().company_names',
    '$*.csvpaths.*.:uuid("a901-33b9-...")',
    '$acme.csvpaths.:uuid("a901-33b9-...").:index(3)',
    '$acme.csvpaths.:uuid("a901-33b9-...").:index(@which)',
    '$acme.csvpaths.:last().:all()',
    '$acme.results.:all()',
    '$acme.results.:last()',
    '$acme.results.customers/2025:first()',
    '$acme.results.customers/2025:first().invoices',
    '$acme.results.*/2025:first().invoices',
    '$acme.results.*/*/2025:first().invoices',
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
    '$acme.files.:name("100%%done").:data()',
    '$acme.files.:name("100%20done").:data()',
    '$acme.files.:name("say \\"hi\\"").:data()',
    '$acme.results.:name(/^[^M].*/)/2025:first().invoices',
    '$acme.results.:name(/^(?:Mon|Tue)day$/)/2025:first().invoices',
    '$acme.results.:name(/^(Mon|Tue)day$/)/2025:first().invoices',
    '$acme.results.:name(/contains"quote/)/2025:first().invoices',
]


@pytest.mark.parametrize("reference", SPEC_EXAMPLES)
def test_spec_examples_round_trip(reference):
    r = ReferenceParser3(string=reference, csvpaths=CSVPATHS)
    assert r.ref_string == reference


class TestConstruction:
    @pytest.mark.parametrize("bad_string", [None, ""])
    def test_rejects_none_or_empty_string(self, bad_string):
        with pytest.raises(ValueError):
            ReferenceParser3(string=bad_string, csvpaths=CSVPATHS)

    def test_rejects_none_csvpaths(self):
        with pytest.raises(ValueError):
            ReferenceParser3(string="$acme.results.a", csvpaths=None)

    def test_holds_original_reference_string(self):
        r = ReferenceParser3(string="$acme.results.a", csvpaths=CSVPATHS)
        assert r.reference == "$acme.results.a"

    def test_csvpaths_is_held(self):
        sentinel = object()
        r = ReferenceParser3(string="$acme.results.a", csvpaths=sentinel)
        assert r.csvpaths is sentinel

    def test_csvpaths_settable_after_construction(self):
        r = ReferenceParser3(string="$acme.results.a", csvpaths=CSVPATHS)
        sentinel = object()
        r.csvpaths = sentinel
        assert r.csvpaths is sentinel


class TestProperties:
    def test_top_level_properties(self):
        r = ReferenceParser3(
            string="$acme.files.Q2/test-data.:last()", csvpaths=CSVPATHS
        )
        assert r.root_major == "acme"
        assert r.datatype == "files"
        assert r.name_one.path == ["Q2", "test-data"]
        assert r.name_three.functions[0].name == "last"

    def test_name_two_passthrough_from_name_one(self):
        r = ReferenceParser3(
            string='$acme.files.*#my_worksheet.:type("xlsx")', csvpaths=CSVPATHS
        )
        assert r.name_two == "my_worksheet"

    def test_name_two_none_when_absent(self):
        r = ReferenceParser3(string="$acme.results.a", csvpaths=CSVPATHS)
        assert r.name_two is None

    def test_parsed_is_a_reference3(self):
        r = ReferenceParser3(string="$acme.results.a", csvpaths=CSVPATHS)
        assert isinstance(r.parsed, Reference3)


class TestNameThreeRequiredness:
    @pytest.mark.parametrize("datatype", ["files", "csvpaths"])
    def test_missing_name_three_raises_for_files_and_csvpaths(self, datatype):
        with pytest.raises(ReferenceException3):
            ReferenceParser3(string=f"$acme.{datatype}.a", csvpaths=CSVPATHS)

    def test_missing_name_three_is_fine_for_results(self):
        r = ReferenceParser3(string="$acme.results.a", csvpaths=CSVPATHS)
        assert r.name_three is None

    def test_reference_exception_is_not_wrapped_by_lark(self):
        # regression: check_valid() runs outside Transformer.transform(),
        # specifically so a violation surfaces as ReferenceException3
        # itself, not wrapped in lark.exceptions.VisitError.
        try:
            ReferenceParser3(string="$acme.files.a", csvpaths=CSVPATHS)
        except ReferenceException3:
            pass
        else:
            pytest.fail("expected ReferenceException3")
