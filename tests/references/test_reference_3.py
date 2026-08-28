import pytest

from csvpath.references.reference_3 import (
    FunctionCall3,
    InterpolatedString3,
    NameOne3,
    NameThree3,
    Reference3,
    Regex3,
    Star3,
    Variable3,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3


#
# low-level unit tests for the references-v3 object graph itself --
# construction, equality, and str rendering -- independent of the Lark
# grammar/transformer. these are the building blocks the transformer
# tests and ReferenceParser3 tests build on.
#


class TestStar3:
    def test_all_instances_equal(self):
        assert Star3() == Star3()

    def test_not_equal_to_other_types(self):
        assert Star3() != "*"
        assert Star3() != None  # noqa: E711

    def test_str(self):
        assert str(Star3()) == "*"


class TestVariable3:
    def test_holds_name(self):
        assert Variable3(name="customer").name == "customer"

    @pytest.mark.parametrize("bad_name", [None, ""])
    def test_rejects_none_or_empty_name(self, bad_name):
        with pytest.raises(ValueError):
            Variable3(name=bad_name)

    def test_equality(self):
        assert Variable3(name="x") == Variable3(name="x")
        assert Variable3(name="x") != Variable3(name="y")

    def test_str(self):
        assert str(Variable3(name="customer")) == "@customer"


class TestRegex3:
    def test_holds_pattern(self):
        assert Regex3(pattern="^abc$").pattern == "^abc$"

    def test_rejects_none_pattern(self):
        with pytest.raises(ValueError):
            Regex3(pattern=None)

    def test_allows_empty_pattern(self):
        # an empty regex, "//", is structurally odd but not this class's
        # job to reject -- only None is a bounds violation here.
        assert Regex3(pattern="").pattern == ""

    def test_equality(self):
        assert Regex3(pattern="a.*b") == Regex3(pattern="a.*b")
        assert Regex3(pattern="a.*b") != Regex3(pattern="c.*d")

    def test_str_adds_delimiters(self):
        assert str(Regex3(pattern="^abc$")) == "/^abc$/"


class TestFunctionCall3:
    def test_rejects_none_or_empty_name(self):
        with pytest.raises(ValueError):
            FunctionCall3(name="")
        with pytest.raises(ValueError):
            FunctionCall3(name=None)

    def test_no_arg(self):
        f = FunctionCall3(name="all")
        assert f.name == "all"
        assert f.arg is None
        assert str(f) == ":all()"

    def test_string_arg_renders_quoted(self):
        f = FunctionCall3(name="name", arg="Acme")
        assert str(f) == ':name("Acme")'

    def test_string_arg_with_quote_and_backslash_escapes_on_render(self):
        f = FunctionCall3(name="name", arg='say "hi" \\ bye')
        assert str(f) == ':name("say \\"hi\\" \\\\ bye")'

    def test_int_arg_renders_bare(self):
        f = FunctionCall3(name="index", arg=7)
        assert str(f) == ":index(7)"

    def test_star_arg(self):
        f = FunctionCall3(name="name", arg=Star3())
        assert str(f) == ":name(*)"

    def test_variable_arg(self):
        f = FunctionCall3(name="index", arg=Variable3(name="which"))
        assert str(f) == ":index(@which)"

    def test_regex_arg(self):
        f = FunctionCall3(name="name", arg=Regex3(pattern="^abc$"))
        assert str(f) == ":name(/^abc$/)"

    def test_nested_function_arg(self):
        inner = FunctionCall3(name="index", arg=0)
        f = FunctionCall3(name="from", arg=inner)
        assert str(f) == ":from(:index(0))"

    def test_equality(self):
        assert FunctionCall3(name="last") == FunctionCall3(name="last")
        assert FunctionCall3(name="last") != FunctionCall3(name="first")
        assert FunctionCall3(name="index", arg=7) != FunctionCall3(name="index", arg=8)

    def test_contains_function_named_matches_self(self):
        assert FunctionCall3(name="idchain", arg="x").contains_function_named("idchain")

    def test_contains_function_named_matches_nested(self):
        f = FunctionCall3(name="errors", arg=FunctionCall3(name="idchain", arg="x"))
        assert f.contains_function_named("idchain")
        assert not f.contains_function_named("data")

    def test_contains_function_named_false_when_arg_not_a_function(self):
        f = FunctionCall3(name="from", arg=FunctionCall3(name="index", arg=0))
        assert not f.contains_function_named("idchain")

    def test_contains_function_named_false_with_no_arg(self):
        assert not FunctionCall3(name="all").contains_function_named("idchain")

    def test_check_valid_passes_with_no_arg(self):
        FunctionCall3(name="all").check_valid()  # should not raise

    def test_check_valid_passes_with_a_plain_string_arg(self):
        FunctionCall3(name="name", arg="Acme").check_valid()  # should not raise

    def test_check_valid_recurses_into_a_nested_function_arg(self):
        bad_interpolation = InterpolatedString3(
            parts=["x-", FunctionCall3(name="first")]
        )
        outer = FunctionCall3(
            name="from", arg=FunctionCall3(name="name", arg=bad_interpolation)
        )
        with pytest.raises(ReferenceException3):
            outer.check_valid()

    def test_check_valid_recurses_into_an_interpolated_string_arg(self):
        bad_interpolation = InterpolatedString3(
            parts=["x-", FunctionCall3(name="first")]
        )
        f = FunctionCall3(name="name", arg=bad_interpolation)
        with pytest.raises(ReferenceException3):
            f.check_valid()


class TestInterpolatedString3:
    def test_rejects_none_or_empty_parts(self):
        with pytest.raises(ValueError):
            InterpolatedString3(parts=None)
        with pytest.raises(ValueError):
            InterpolatedString3(parts=[])

    def test_check_valid_accepts_a_bare_variable(self):
        s = InterpolatedString3(parts=["x-", Variable3(name="company")])
        s.check_valid()  # should not raise

    def test_check_valid_rejects_a_pointer_role_function(self):
        # :first() is POINTER -- pointers act on scope, not on
        # producing a plain value to interpolate.
        s = InterpolatedString3(parts=["x-", FunctionCall3(name="first")])
        with pytest.raises(ReferenceException3):
            s.check_valid()

    def test_check_valid_rejects_a_context_setter_role_function(self):
        # :all() is CONTEXT_SETTER -- same reasoning as pointers.
        s = InterpolatedString3(parts=["x-", FunctionCall3(name="all")])
        with pytest.raises(ReferenceException3):
            s.check_valid()

    def test_check_valid_rejects_an_unknown_function(self):
        s = InterpolatedString3(
            parts=["x-", FunctionCall3(name="not_a_real_function")]
        )
        with pytest.raises(ReferenceException3):
            s.check_valid()

    def test_check_valid_accepts_a_value_role_function(self):
        from csvpath.references.functions.function_3 import Function3
        from csvpath.references.functions.reference_function_factory_3 import (
            ReferenceFunctionFactory,
        )

        class _Year3ForTest(Function3):
            NAME = "year_for_test"
            SUMMARY = "test-only value function"
            ROLE = Function3.VALUE
            DATATYPES = ()
            ARG_TYPES = ()
            ARG_REQUIRED = False

        ReferenceFunctionFactory.add_function(_Year3ForTest)
        try:
            s = InterpolatedString3(
                parts=["x-", FunctionCall3(name="year_for_test")]
            )
            s.check_valid()  # should not raise
        finally:
            del ReferenceFunctionFactory._FUNCTIONS["year_for_test"]

    def test_equality(self):
        assert InterpolatedString3(parts=["a"]) == InterpolatedString3(parts=["a"])
        assert InterpolatedString3(parts=["a"]) != InterpolatedString3(parts=["b"])

    def test_str_renders_variable_in_braces(self):
        s = InterpolatedString3(parts=["partner-", Variable3(name="company")])
        assert str(s) == "partner-{@company}"

    def test_str_escapes_literal_braces(self):
        s = InterpolatedString3(parts=["a{b}c"])
        assert str(s) == "a{{b}}c"

    def test_str_renders_function_in_braces(self):
        s = InterpolatedString3(parts=["x-", FunctionCall3(name="first")])
        assert str(s) == "x-{:first()}"


class TestNameOne3:
    def test_rejects_empty_path(self):
        with pytest.raises(ValueError):
            NameOne3(path=[])
        with pytest.raises(ValueError):
            NameOne3(path=None)

    def test_literal_path_only(self):
        n = NameOne3(path=["Q2", "test-data"])
        assert str(n) == "Q2/test-data"

    def test_path_with_star(self):
        n = NameOne3(path=[Star3()])
        assert str(n) == "*"

    def test_path_with_function_segment(self):
        n = NameOne3(path=[FunctionCall3(name="all")])
        assert str(n) == ":all()"

    def test_with_name_two(self):
        n = NameOne3(path=[Star3()], name_two="my_worksheet")
        assert str(n) == "*#my_worksheet"

    def test_with_trailing_functions(self):
        n = NameOne3(
            path=["Q2"],
            functions=[FunctionCall3(name="last"), FunctionCall3(name="first")],
        )
        assert str(n) == "Q2:last():first()"

    def test_full_shape(self):
        n = NameOne3(
            path=[Star3()],
            name_two="ws",
            functions=[FunctionCall3(name="type", arg="xlsx")]
        )
        assert str(n) == '*#ws:type("xlsx")'

    def test_equality(self):
        assert NameOne3(path=["a"]) == NameOne3(path=["a"])
        assert NameOne3(path=["a"]) != NameOne3(path=["b"])
        assert NameOne3(path=["a"], name_two="w") != NameOne3(path=["a"])


class TestNameThree3:
    def test_rejects_empty_body_and_functions(self):
        with pytest.raises(ValueError):
            NameThree3()

    def test_body_only(self):
        n = NameThree3(body="invoices")
        assert str(n) == "invoices"

    def test_body_star(self):
        n = NameThree3(body=Star3())
        assert str(n) == "*"

    def test_functions_only(self):
        n = NameThree3(functions=[FunctionCall3(name="all")])
        assert str(n) == ":all()"

    def test_body_and_functions(self):
        n = NameThree3(body="invoices", functions=[FunctionCall3(name="data")])
        assert str(n) == "invoices:data()"

    def test_equality(self):
        assert NameThree3(body="a") == NameThree3(body="a")
        assert NameThree3(body="a") != NameThree3(body="b")


class TestReference3:
    def _name_one(self, *path):
        return NameOne3(path=list(path))

    def test_rejects_none_root_major(self):
        with pytest.raises(ValueError):
            Reference3(
                root_major=None,
                datatype=Reference3.FILES,
                name_one=self._name_one("a"),
                name_three=NameThree3(body="v1"),
            )

    def test_rejects_unknown_datatype(self):
        with pytest.raises(ValueError):
            Reference3(
                root_major="acme",
                datatype="bogus",
                name_one=self._name_one("a"),
            )

    def test_rejects_none_name_one(self):
        with pytest.raises(ValueError):
            Reference3(root_major="acme", datatype=Reference3.FILES, name_one=None)

    @pytest.mark.parametrize(
        "datatype", [Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS]
    )
    def test_check_valid_allows_missing_name_three_for_every_datatype(self, datatype):
        # name_three is optional everywhere (per "creating references
        # v3.txt"'s STRUCTURE section) -- name_one alone is a legal,
        # resolvable reference on its own for files/csvpaths too now,
        # not just results.
        r = Reference3(
            root_major="acme", datatype=datatype, name_one=self._name_one("a")
        )
        r.check_valid()  # should not raise

    def test_check_valid_passes_when_name_three_present(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one("a"),
            name_three=NameThree3(body="v1"),
        )
        r.check_valid()  # should not raise

    def test_check_valid_accepts_a_function_valued_root_major(self):
        # added 2026-08-27, for :regex() at root_major -- a plain,
        # structurally-valid FunctionCall3 there should not raise.
        r = Reference3(
            root_major=FunctionCall3(name="regex", arg="acme_.*"),
            datatype=Reference3.FILES,
            name_one=self._name_one("a"),
        )
        r.check_valid()  # should not raise

    def test_check_valid_recurses_into_root_majors_own_function(self):
        # root_major's own FunctionCall3.check_valid() gets called too
        # (not just name_one/name_three's) -- proven here via a nested
        # InterpolatedString3 containing an illegal POINTER-role
        # function, the same recursion TestFunctionCall3's own
        # equivalent test proves for an ordinary name_one segment.
        bad = InterpolatedString3(parts=["x-", FunctionCall3(name="first")])
        r = Reference3(
            root_major=FunctionCall3(name="regex", arg=bad),
            datatype=Reference3.FILES,
            name_one=self._name_one("a"),
        )
        with pytest.raises(ReferenceException3):
            r.check_valid()

    def test_check_valid_rejects_bare_trailing_star(self):
        # "*" alone: "any of the data that ___" with nothing to
        # complete it -- no name_three, no trailing function on
        # name_one, and the star is name_one's last path segment.
        r = Reference3(
            root_major="acme", datatype=Reference3.FILES, name_one=self._name_one(Star3())
        )
        with pytest.raises(ReferenceException3):
            r.check_valid()

    def test_check_valid_rejects_star_trailing_after_a_literal_segment(self):
        # the star being last is what matters, not whether it is alone
        # -- "orders/*" still dangles the same way "*" does.
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one("orders", Star3()),
        )
        with pytest.raises(ReferenceException3):
            r.check_valid()

    def test_check_valid_allows_star_followed_by_a_literal_segment(self):
        # "*/orders" completes the sentence with the literal segment
        # that follows the star -- only a *trailing*, un-followed star
        # is a problem.
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one(Star3(), "orders"),
        )
        r.check_valid()  # should not raise

    def test_check_valid_allows_star_with_name_ones_own_trailing_function(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=NameOne3(
                path=[Star3()], functions=[FunctionCall3(name="first")]
            ),
        )
        r.check_valid()  # should not raise

    def test_check_valid_allows_star_with_name_three(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one(Star3()),
            name_three=NameThree3(functions=[FunctionCall3(name="first")]),
        )
        r.check_valid()  # should not raise

    def test_check_valid_allows_bare_all_function(self):
        # :all() is not equivalent to "*" -- it is already a complete
        # instruction ("get me all of them!"), not a dangling clause,
        # so it is fine bare with no name_three and no other function.
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one(FunctionCall3(name="all")),
        )
        r.check_valid()  # should not raise

    def test_str_without_name_three(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.RESULTS,
            name_one=self._name_one("a"),
        )
        assert str(r) == "$acme.results.a"

    def test_str_with_name_three(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one("a"),
            name_three=NameThree3(body="v1"),
        )
        assert str(r) == "$acme.files.a.v1"

    def test_str_with_star_root_major(self):
        r = Reference3(
            root_major=Star3(),
            datatype=Reference3.RESULTS,
            name_one=self._name_one("a"),
        )
        assert str(r) == "$*.results.a"

    def test_equality(self):
        a = Reference3(
            root_major="acme", datatype=Reference3.RESULTS, name_one=self._name_one("a")
        )
        b = Reference3(
            root_major="acme", datatype=Reference3.RESULTS, name_one=self._name_one("a")
        )
        c = Reference3(
            root_major="acme", datatype=Reference3.RESULTS, name_one=self._name_one("b")
        )
        assert a == b
        assert a != c


class TestResolveKind:
    def _name_one(self, *path, functions=None):
        return NameOne3(path=list(path), functions=functions)

    def test_first_party_when_no_name_three_and_no_name_one_functions(self):
        r = Reference3(
            root_major="acme", datatype=Reference3.RESULTS, name_one=self._name_one("a")
        )
        assert r.resolve_kind == Reference3.FIRST_PARTY

    def test_first_party_for_ordinary_selector_function_with_nested_arg(self):
        # :from(:index(0)) is still a version/range selector, not a
        # value extraction -- a nested function arg alone must not
        # trigger anything beyond FIRST_PARTY.
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one("a"),
            name_three=NameThree3(
                functions=[
                    FunctionCall3(name="from", arg=FunctionCall3(name="index", arg=0))
                ]
            ),
        )
        assert r.resolve_kind == Reference3.FIRST_PARTY

    def test_metadata_file_for_plain_well_known_file_function(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.RESULTS,
            name_one=self._name_one("a"),
            name_three=NameThree3(functions=[FunctionCall3(name="errors")]),
        )
        assert r.resolve_kind == Reference3.METADATA_FILE

    def test_metadata_field_when_value_locator_nested_in_terminal_function(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.RESULTS,
            name_one=self._name_one("a"),
            name_three=NameThree3(
                functions=[
                    FunctionCall3(
                        name="errors",
                        arg=FunctionCall3(name="idchain", arg="add[0]string[2]"),
                    )
                ]
            ),
        )
        assert r.resolve_kind == Reference3.METADATA_FIELD

    def test_uses_name_one_functions_when_name_three_is_absent(self):
        # name_one alone is now a legal terminus (name_three optional
        # everywhere), so its own trailing function chain is what
        # resolve_kind must inspect when there is no name_three.
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one("a", functions=[FunctionCall3(name="errors")]),
        )
        assert r.resolve_kind == Reference3.METADATA_FILE

    def test_uses_name_one_path_segment_function_when_it_is_the_sole_content(self):
        # a "path-less, function-only" name_one (e.g. ":manifest()" or
        # ":all()" occupying the sole path segment) has its function in
        # .path, not .functions -- resolve_kind must look there too, not
        # just at the trailing chain, or a bare "$acme.files.:manifest()"
        # would be misclassified as FIRST_PARTY.
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one(FunctionCall3(name="manifest")),
        )
        assert r.resolve_kind == Reference3.METADATA_FILE


class TestTerminalFunctions:
    # extracted 2026-08-26 from resolve_kind's own inline computation --
    # same traversal, now a public property ReferenceExpression3's own
    # paths-vs-values classifier also relies on.
    def _name_one(self, *path, functions=None):
        return NameOne3(path=list(path), functions=functions)

    def test_empty_when_no_functions_anywhere(self):
        r = Reference3(
            root_major="acme", datatype=Reference3.RESULTS, name_one=self._name_one("a")
        )
        assert r.terminal_functions == []

    def test_uses_name_three_functions_when_present(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.RESULTS,
            name_one=self._name_one("a"),
            name_three=NameThree3(functions=[FunctionCall3(name="errors")]),
        )
        names = [f.name for f in r.terminal_functions]
        assert names == ["errors"]

    def test_uses_name_one_functions_when_name_three_absent(self):
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one("a", functions=[FunctionCall3(name="uuid")]),
        )
        names = [f.name for f in r.terminal_functions]
        assert names == ["uuid"]

    def test_includes_a_function_valued_path_segment(self):
        # a "path-less, function-only" name_one has its function in
        # .path, not .functions -- terminal_functions must include it.
        r = Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=self._name_one(
                FunctionCall3(name="last"), functions=[FunctionCall3(name="uuid")]
            ),
        )
        names = [f.name for f in r.terminal_functions]
        assert names == ["last", "uuid"]
