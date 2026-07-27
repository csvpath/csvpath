import pytest

from csvpath.references.reference_3 import (
    FunctionCall3,
    Regex3,
    Star3,
    Variable3,
)
from csvpath.references.reference_grammar_3 import QueryParser3
from csvpath.references.reference_transformer_3 import Reference3Transformer


#
# tests that a parse tree actually gets turned into the structure we
# expect -- one representative case per interesting grammar shape,
# rather than re-running the whole grammar-level corpus (that's already
# covered, at the syntax-only level, by test_references_3_grammar.py).
#


@pytest.fixture(scope="module")
def parser() -> QueryParser3:
    return QueryParser3()


def build(parser, query):
    tree = parser.parse(query)
    return Reference3Transformer().transform(tree)


class TestRootMajorAndDatatype:
    def test_literal_root_major(self, parser):
        r = build(parser, "$acme.results.a")
        assert r.root_major == "acme"
        assert r.datatype == "results"

    def test_star_root_major(self, parser):
        r = build(parser, "$*.results.a")
        assert r.root_major == Star3()


class TestNameOnePath:
    def test_single_literal_segment(self, parser):
        r = build(parser, "$acme.files.somefile.v1")
        assert r.name_one.path == ["somefile"]

    def test_multi_segment_literal_path(self, parser):
        r = build(parser, "$acme.files.Q2/test-data.v1")
        assert r.name_one.path == ["Q2", "test-data"]

    def test_star_segment(self, parser):
        r = build(parser, "$acme.files.*.v1")
        assert r.name_one.path == [Star3()]

    def test_function_as_sole_segment_no_trailing_chain(self, parser):
        # this is exactly the shape that used to be ambiguous (bare
        # func_chain vs. path_prefix's single function-segment) before
        # the grammar fix -- confirm it builds a single-segment path,
        # not a two-item path or something split oddly.
        r = build(parser, "$acme.files.:all().v1")
        assert r.name_one.path == [FunctionCall3(name="all")]
        assert r.name_one.functions == []

    def test_function_segment_mixed_with_literal_path(self, parser):
        r = build(parser, '$acme.files.:quarter()/:name("live data").v1')
        assert r.name_one.path == [
            FunctionCall3(name="quarter"),
            FunctionCall3(name="name", arg="live data"),
        ]

    def test_multiple_functions_no_path_split_between_segment_and_chain(self, parser):
        # ":before():after():index(3)" as name_one: no slashes at all, so
        # this can only come from path_prefix's one-segment case (the
        # first function) plus a trailing func_chain (the rest) -- there
        # is no other way to produce it now that the ambiguous bare
        # func_chain alternative is gone.
        r = build(
            parser,
            '$acme.csvpaths.:before(:yesterday()):after(:date("2024-08-01")):index(3).v1',
        )
        assert r.name_one.path == [FunctionCall3(name="before", arg=FunctionCall3(name="yesterday"))]
        assert r.name_one.functions == [
            FunctionCall3(name="after", arg=FunctionCall3(name="date", arg="2024-08-01")),
            FunctionCall3(name="index", arg=3),
        ]


class TestNameOneWorksheetAndFunctions:
    def test_name_two_worksheet(self, parser):
        r = build(parser, '$acme.files.*#my_worksheet.:type("xlsx")')
        assert r.name_one.name_two == "my_worksheet"

    def test_trailing_function_chain(self, parser):
        # note the dot before the functions here puts them in name_three,
        # not name_one -- see test_name_one_can_carry_its_own_trailing_
        # function_chain below for functions attached to name_one itself.
        r = build(parser, "$acme.files.*.:last():before(:today())")
        assert r.name_one.path == [Star3()]
        assert r.name_one.functions == []
        assert r.name_three.functions == [
            FunctionCall3(name="last"),
            FunctionCall3(name="before", arg=FunctionCall3(name="today")),
        ]

    def test_name_one_can_carry_its_own_trailing_function_chain(self, parser):
        # no dot between "*" and the functions -- these belong to
        # name_one, with "v1" as a separate name_three.
        r = build(parser, "$acme.files.*:last():before(:today()).v1")
        assert r.name_one.path == [Star3()]
        assert r.name_one.functions == [
            FunctionCall3(name="last"),
            FunctionCall3(name="before", arg=FunctionCall3(name="today")),
        ]
        assert r.name_three.body == "v1"


class TestNameThree:
    def test_literal_body_only(self, parser):
        r = build(parser, "$acme.files.a.invoices")
        assert r.name_three.body == "invoices"
        assert r.name_three.functions == []

    def test_star_body(self, parser):
        r = build(parser, "$acme.results.customers/:from(:index(-1)).*:type(\"parquet\")")
        assert r.name_three.body == Star3()
        assert r.name_three.functions == [FunctionCall3(name="type", arg="parquet")]

    def test_bare_function_chain(self, parser):
        r = build(parser, "$acme.results.a.:all()")
        assert r.name_three.body is None
        assert r.name_three.functions == [FunctionCall3(name="all")]

    def test_body_with_trailing_functions(self, parser):
        r = build(parser, "$acme.results.customers/2025:first().invoices:data()")
        assert r.name_three.body == "invoices"
        assert r.name_three.functions == [FunctionCall3(name="data")]

    def test_absent_name_three(self, parser):
        r = build(parser, "$acme.results.a")
        assert r.name_three is None


class TestFunctionArgs:
    def test_string_arg(self, parser):
        r = build(parser, '$acme.files.a.:name("Acme")')
        assert r.name_three.functions[0].arg == "Acme"

    def test_signed_int_arg(self, parser):
        r = build(parser, "$acme.files.*.:index(7)")
        assert r.name_three.functions[0].arg == 7

    def test_negative_signed_int_arg(self, parser):
        # the dot before :at(-1) puts it in name_three, not name_one.
        r = build(parser, "$acme.files.*#w.:at(-1)")
        assert r.name_three.functions[0].arg == -1

    def test_variable_arg(self, parser):
        r = build(parser, "$acme.files.Q2/:name(@customer).v1")
        assert r.name_one.path[1].arg == Variable3(name="customer")

    def test_star_arg(self, parser):
        r = build(parser, "$acme.files.Q2/:name(*).v1")
        assert r.name_one.path[1].arg == Star3()

    def test_regex_arg(self, parser):
        r = build(parser, "$acme.results.:name(/^[^M].*/)/2025:first().invoices")
        assert r.name_one.path[0].arg == Regex3(pattern="^[^M].*")

    def test_nested_function_arg(self, parser):
        r = build(parser, "$acme.files.*.:from(:index(0)):to(@index)")
        assert r.name_three.functions[0] == FunctionCall3(
            name="from", arg=FunctionCall3(name="index", arg=0)
        )
        assert r.name_three.functions[1] == FunctionCall3(
            name="to", arg=Variable3(name="index")
        )

    def test_string_with_escaped_quote_and_backslash(self, parser):
        r = build(parser, '$acme.files.a.:name("say \\"hi\\"")')
        assert r.name_three.functions[0].arg == 'say "hi"'
