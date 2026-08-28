import pytest

from csvpath.references.reference_3 import (
    FunctionCall3,
    NameOne3,
    NameThree3,
    Reference3,
    Regex3,
    Star3,
    Variable3,
)
from csvpath.references.reference_exceptions_3 import ReferenceRuntimeException3
from csvpath.references.reference_finder_3 import ReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.reference_results_3 import ReferenceResult3, ReferenceResults3

CSVPATHS = object()


class _DummyFinder(ReferenceFinder3):
    """minimal concrete finder for exercising the shared resolve()/
    resolve_from() logic on the ABC -- query() and _extract_data() are
    the only datatype-specific hooks, so a fixed fake result set and a
    deterministic extraction are enough."""

    def __init__(self, *, csvpaths, ref, variables: dict | None = None) -> None:
        super().__init__(csvpaths=csvpaths, ref=ref, variables=variables)
        self.query_call_count = 0

    def query(self) -> ReferenceResults3:
        self.query_call_count += 1
        return ReferenceResults3(
            results=[
                ReferenceResult3(path="p1", uuid="u1"),
                ReferenceResult3(path="p2", uuid="u2"),
            ]
        )

    def _extract_data(self, result: ReferenceResult3):
        return f"data-for-{result.path}"


def _ref(reference: str) -> ReferenceParser3:
    return ReferenceParser3(string=reference, csvpaths=CSVPATHS)


class TestConstruction:
    def test_rejects_none_csvpaths(self):
        with pytest.raises(ValueError):
            _DummyFinder(csvpaths=None, ref=_ref("$acme.results.a"))

    def test_rejects_none_ref(self):
        with pytest.raises(ValueError):
            _DummyFinder(csvpaths=CSVPATHS, ref=None)

    def test_cannot_instantiate_the_abc_directly(self):
        with pytest.raises(TypeError):
            ReferenceFinder3(csvpaths=CSVPATHS, ref=_ref("$acme.results.a"))

    def test_holds_ref_and_csvpaths(self):
        ref = _ref("$acme.results.a")
        f = _DummyFinder(csvpaths=CSVPATHS, ref=ref)
        assert f.ref is ref
        assert f.csvpaths is CSVPATHS


class TestApplyPointer:
    # shared by every finder that reads a flat manifest array (files,
    # csvpaths) -- moved onto the ABC once there were two real
    # consumers, not just one.
    def test_first(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "first"})(), ["a", "b", "c"]
        ) == "a"

    def test_last(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "last"})(), ["a", "b", "c"]
        ) == "c"

    def test_index(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "index", "arg": 1})(), ["a", "b", "c"]
        ) == "b"

    def test_index_out_of_range_returns_none(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "index", "arg": 99})(), ["a", "b", "c"]
        ) is None

    def test_empty_candidates_returns_none(self):
        assert ReferenceFinder3._apply_pointer(
            type("P", (), {"name": "first"})(), []
        ) is None

    def test_unsupported_pointer_name_raises(self):
        from csvpath.references.reference_exceptions_3 import ReferenceException3

        with pytest.raises(ReferenceException3):
            ReferenceFinder3._apply_pointer(
                type("P", (), {"name": "bogus"})(), ["a"]
            )


class TestIsBarePointerReference:
    # shared by every finder that needs to detect a ":manifest()"-style,
    # sole-content name_one shape (files, csvpaths) -- see :manifest()'s
    # own query() branch in each finder, which must bypass ordinary
    # "which file"/"which version" narrowing entirely for this shape.
    @staticmethod
    def _ref(name_one, name_three=None) -> Reference3:
        return Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=name_one,
            name_three=name_three,
        )

    def test_true_for_bare_sole_function(self):
        r = self._ref(NameOne3(path=[FunctionCall3(name="manifest")]))
        assert ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_for_different_function_name(self):
        r = self._ref(NameOne3(path=[FunctionCall3(name="all")]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_when_function_has_an_arg(self):
        r = self._ref(NameOne3(path=[FunctionCall3(name="manifest", arg="x")]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_with_extra_path_segment(self):
        r = self._ref(NameOne3(path=["a", FunctionCall3(name="manifest")]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_with_trailing_functions(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="manifest")],
                functions=[FunctionCall3(name="first")],
            )
        )
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_when_name_three_present(self):
        r = self._ref(
            NameOne3(path=[FunctionCall3(name="manifest")]),
            name_three=NameThree3(body="v1"),
        )
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")

    def test_false_for_literal_path_segment(self):
        r = self._ref(NameOne3(path=["manifest"]))
        assert not ReferenceFinder3._is_bare_pointer_reference(r, "manifest")


class TestPointerBeforeManifest:
    # shared by every finder that supports ordinal indexing into a
    # global ledger (Rule 1b) -- files/csvpaths/results all read a flat
    # array in arrival order, so a pointer riding alongside the bare
    # :manifest() (e.g. ":last():manifest()", parsed as name_one.path
    # == [:last()], name_one.functions == [:manifest()]) means the same
    # thing everywhere -- in either order (see
    # test_true_for_manifest_then_pointer below; order-insensitivity
    # was missing and fixed 2026-08-10).
    @staticmethod
    def _ref(name_one, name_three=None) -> Reference3:
        return Reference3(
            root_major="acme",
            datatype=Reference3.FILES,
            name_one=name_one,
            name_three=name_three,
        )

    def test_true_for_pointer_then_bare_manifest(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="last")],
                functions=[FunctionCall3(name="manifest")],
            )
        )
        pointer = ReferenceFinder3._pointer_before_manifest(r, "manifest")
        assert pointer is not None
        assert pointer.name == "last"

    def test_index_pointer_keeps_its_arg(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="index", arg=3)],
                functions=[FunctionCall3(name="manifest")],
            )
        )
        pointer = ReferenceFinder3._pointer_before_manifest(r, "manifest")
        assert pointer.name == "index"
        assert pointer.arg == 3

    def test_none_when_no_trailing_function(self):
        r = self._ref(NameOne3(path=[FunctionCall3(name="last")]))
        assert ReferenceFinder3._pointer_before_manifest(r, "manifest") is None

    def test_true_for_manifest_then_pointer(self):
        # the reverse order -- ":manifest():last()" -- means the same
        # thing as ":last():manifest()". Confirmed missing 2026-08-10:
        # this used to only recognize pointer-first.
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="manifest")],
                functions=[FunctionCall3(name="last")],
            )
        )
        pointer = ReferenceFinder3._pointer_before_manifest(r, "manifest")
        assert pointer is not None
        assert pointer.name == "last"

    def test_none_when_both_positions_are_pointers(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="last")],
                functions=[FunctionCall3(name="first")],
            )
        )
        assert ReferenceFinder3._pointer_before_manifest(r, "manifest") is None

    def test_none_when_path_segment_is_not_a_pointer(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="all")],
                functions=[FunctionCall3(name="manifest")],
            )
        )
        assert ReferenceFinder3._pointer_before_manifest(r, "manifest") is None

    def test_none_when_trailing_function_is_not_the_named_one(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="last")],
                functions=[FunctionCall3(name="definition")],
            )
        )
        assert ReferenceFinder3._pointer_before_manifest(r, "manifest") is None

    def test_none_when_trailing_function_has_an_arg(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="last")],
                functions=[FunctionCall3(name="manifest", arg="x")],
            )
        )
        assert ReferenceFinder3._pointer_before_manifest(r, "manifest") is None

    def test_none_when_name_three_present(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="last")],
                functions=[FunctionCall3(name="manifest")],
            ),
            name_three=NameThree3(body="v1"),
        )
        assert ReferenceFinder3._pointer_before_manifest(r, "manifest") is None

    def test_none_with_extra_path_segments(self):
        r = self._ref(
            NameOne3(
                path=[FunctionCall3(name="last"), "extra"],
                functions=[FunctionCall3(name="manifest")],
            )
        )
        assert ReferenceFinder3._pointer_before_manifest(r, "manifest") is None


class TestQueryWellKnownFile:
    # shared query() branch for a fixed, home-directory-scoped JSON
    # resource (manifest.json, definition.json) -- both files and
    # csvpaths route :manifest()/:definition() through this.
    def test_returns_one_result_with_no_uuid(self):
        results = ReferenceFinder3._query_well_known_file("some/home", "manifest.json")
        assert results.files == ["some/home/manifest.json"]
        assert results.results[0].uuid is None


class TestReadWellKnownFile:
    def test_reads_raw_bytes_when_the_file_exists(self, tmp_path):
        content = b'{"a": 1}'
        path = tmp_path / "definition.json"
        path.write_bytes(content)
        assert ReferenceFinder3._read_well_known_file(str(path)) == content

    def test_returns_none_when_the_file_does_not_exist(self, tmp_path):
        missing = tmp_path / "definition.json"
        assert ReferenceFinder3._read_well_known_file(str(missing)) is None


class TestFindByIdentity:
    # shared by every finder whose name_three does an identity lookup
    # (csvpaths' named_paths_identities, results' per-statement
    # directory names).
    def test_matches_named_identity(self):
        assert ReferenceFinder3._find_by_identity("b", ["a", "b", "c"]) == 1

    def test_matches_stringified_index_identity(self):
        assert ReferenceFinder3._find_by_identity("0", ["0", "named"]) == 0

    def test_no_match_returns_none(self):
        assert ReferenceFinder3._find_by_identity("nope", ["a", "b"]) is None


class TestExtractFieldValue:
    # shared by every finder resolving a field-accessor function's KEY
    # against a resolved manifest entry or definition.json dict -- see
    # manifest_field_functions_proposal.md, Part A/B.
    def test_reads_a_top_level_key(self):
        assert (
            ReferenceFinder3._extract_field_value({"uuid": "u1"}, "uuid") == "u1"
        )

    def test_walks_a_dotted_path(self):
        container = {"on_arrival": {"named_paths_group": "acme"}}
        assert (
            ReferenceFinder3._extract_field_value(
                container, "on_arrival.named_paths_group"
            )
            == "acme"
        )

    def test_missing_top_level_key_gives_none(self):
        assert ReferenceFinder3._extract_field_value({"uuid": "u1"}, "nope") is None

    def test_missing_nested_key_gives_none(self):
        container = {"on_arrival": {}}
        assert (
            ReferenceFinder3._extract_field_value(
                container, "on_arrival.named_paths_group"
            )
            is None
        )

    def test_none_container_gives_none(self):
        assert ReferenceFinder3._extract_field_value(None, "uuid") is None

    def test_none_key_path_gives_none(self):
        assert ReferenceFinder3._extract_field_value({"uuid": "u1"}, None) is None


class TestFindFieldFunctionCall:
    # shared by files/csvpaths finders to detect a registered field-
    # accessor function (e.g. :uuid()) riding in the same terminal
    # position :manifest() already rides in.
    def test_finds_a_registered_field_function(self):
        calls = [FunctionCall3(name="first"), FunctionCall3(name="uuid")]
        found = ReferenceFinder3._find_field_function_call(calls)
        assert found is not None
        assert found.name == "uuid"

    def test_returns_none_when_no_field_function_present(self):
        calls = [FunctionCall3(name="first"), FunctionCall3(name="manifest")]
        assert ReferenceFinder3._find_field_function_call(calls) is None

    def test_returns_none_for_an_unregistered_name(self):
        calls = [FunctionCall3(name="bogus")]
        assert ReferenceFinder3._find_field_function_call(calls) is None

    def test_empty_list_returns_none(self):
        assert ReferenceFinder3._find_field_function_call([]) is None


class TestResolve:
    # resolve_from() always calls _extract_data() for every result now
    # -- the old resolves_to_data gate is gone from the ABC (it moved
    # into what each concrete finder's own _extract_data() does with
    # Reference3.resolve_kind, not whether it gets called at all).
    REF = "$acme.results.a"

    def test_resolve_extracts_data_for_every_result(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        results = f.resolve()
        assert results.data_for_uuid("u1") == "data-for-p1"
        assert results.data_for_uuid("u2") == "data-for-p2"

    def test_resolve_from_list_narrows_then_only_extracts_the_selection(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        results = f.resolve_from(["p1"])
        assert results.files == ["p1"]
        assert results.results[0].data == "data-for-p1"
        assert f.query_call_count == 1

    def test_resolve_from_a_results3_does_not_requery(self):
        f = _DummyFinder(csvpaths=CSVPATHS, ref=_ref(self.REF))
        preselected = ReferenceResults3(
            results=[ReferenceResult3(path="only-this-one", uuid="uX")]
        )
        results = f.resolve_from(preselected)
        assert results.files == ["only-this-one"]
        assert results.results[0].data == "data-for-only-this-one"
        assert f.query_call_count == 0


def _dummy(variables: dict | None = None) -> _DummyFinder:
    return _DummyFinder(
        csvpaths=CSVPATHS, ref=_ref("$acme.files.:first()"), variables=variables
    )


class TestCompilePathPattern:
    # shared by files/results -- a bare SOURCE == "clock" function
    # (e.g. :year()) is now a legal name_one path segment in its own
    # right (added 2026-08-26), evaluated via compute(); :name("...")'s
    # own arg is run through _resolve_value() too, so a "{...}"-
    # interpolated name works the same way a plain literal one always
    # has. See Year3/ReferenceFinder3._resolve_value()'s own docstrings.
    # No longer staticmethods (since _resolve_value() needs a finder's
    # own registered variables) -- called on a _DummyFinder instance.
    def test_literal_and_star_segments_pass_through_unchanged(self):
        path = _ref("$acme.files.a/*:first()").parsed.name_one.path
        assert _dummy()._compile_path_pattern(path) == ["a", path[1]]

    def test_name_function_unwraps_to_its_literal_string(self):
        path = _ref('$acme.files.:name("orders.csv")').parsed.name_one.path
        assert _dummy()._compile_path_pattern(path) == ["orders.csv"]

    def test_bare_clock_function_evaluates_to_its_computed_value(self):
        path = _ref("$acme.files.:year()").parsed.name_one.path
        from csvpath.util.date_util import DateUtility as daut

        assert _dummy()._compile_path_pattern(path) == [str(daut.now().year)]

    def test_name_function_with_interpolated_clock_call(self):
        path = _ref('$acme.files.:name("orders-{:year()}.csv")').parsed.name_one.path
        from csvpath.util.date_util import DateUtility as daut

        assert _dummy()._compile_path_pattern(path) == [
            f"orders-{daut.now().year}.csv"
        ]

    def test_non_clock_function_segment_is_rejected(self):
        path = _ref("$acme.files.:uuid()").parsed.name_one.path
        with pytest.raises(Exception):
            _dummy()._compile_path_pattern(path)

    def test_name_function_with_a_regex_arg_stays_a_regex3(self):
        # added 2026-08-27 -- unlike a plain string arg, a Regex3 is NOT
        # unwrapped to a str here; it passes through as-is for
        # _segment_matches() to compare with a search(), not equality.
        path = _ref("$acme.files.:name(/orders.*\\.csv/)").parsed.name_one.path
        pattern = _dummy()._compile_path_pattern(path)
        assert len(pattern) == 1
        assert isinstance(pattern[0], Regex3)
        assert pattern[0].pattern == "orders.*\\.csv"


class TestSegmentMatches:
    # shared by every finder's own path-matching primitive (FILES'
    # _matches/_matches_suffix, RESULTS' _matches_prefix/
    # _matches_prefix_at_least) -- added 2026-08-27 alongside :name()'s
    # own Regex3 support.
    def test_star_matches_anything(self):
        assert ReferenceFinder3._segment_matches(Star3(), "whatever") is True

    def test_plain_str_requires_exact_equality(self):
        assert ReferenceFinder3._segment_matches("orders.csv", "orders.csv") is True
        assert ReferenceFinder3._segment_matches("orders.csv", "returns.csv") is False

    def test_regex_searches_not_anchored(self):
        pattern = Regex3(pattern="orders")
        assert ReferenceFinder3._segment_matches(pattern, "my-orders-file.csv") is True
        assert ReferenceFinder3._segment_matches(pattern, "returns.csv") is False

    def test_regex_anchored_pattern_still_works(self):
        pattern = Regex3(pattern=r"^orders.*\.csv$")
        assert ReferenceFinder3._segment_matches(pattern, "orders-2026.csv") is True
        assert ReferenceFinder3._segment_matches(pattern, "not-orders-2026.csv") is False


class TestResolveValue:
    # the "{...}" evaluation half of the same mechanism -- shared by
    # anything that resolves a Function3's own str-typed arg, not just
    # path segments (currently _compile_path_pattern()'s own :name(...)
    # handling).
    def test_plain_string_passes_through_unchanged(self):
        assert _dummy()._resolve_value("plain") == "plain"

    def test_plain_int_passes_through_unchanged(self):
        assert _dummy()._resolve_value(10) == 10

    def test_interpolated_string_with_only_literal_text(self):
        arg = _ref('$acme.files.:name("just-text")').parsed.name_one.path[0].arg
        assert _dummy()._resolve_value(arg) == "just-text"

    def test_interpolated_string_with_a_clock_function(self):
        arg = _ref(
            '$acme.files.:name("prefix-{:year()}-suffix")'
        ).parsed.name_one.path[0].arg
        from csvpath.util.date_util import DateUtility as daut

        assert _dummy()._resolve_value(arg) == (
            f"prefix-{daut.now().year}-suffix"
        )

    def test_non_clock_function_inside_interpolation_is_rejected(self):
        arg = _ref('$acme.files.:name("prefix-{:uuid()}")').parsed.name_one.path[0].arg
        with pytest.raises(Exception):
            _dummy()._resolve_value(arg)

    def test_registered_variable_is_substituted(self):
        arg = _ref(
            '$acme.files.:name("prefix-{@company}-suffix")'
        ).parsed.name_one.path[0].arg
        finder = _dummy({"company": "acme-corp"})
        assert finder._resolve_value(arg) == "prefix-acme-corp-suffix"

    def test_variable_value_need_not_be_a_string(self):
        # compendium 3.12: "a variable can be any Python object, but the
        # variable value will be put into a string context so its
        # __str__ must make sense."
        arg = _ref('$acme.files.:name("count-{@n}")').parsed.name_one.path[0].arg
        finder = _dummy({"n": 42})
        assert finder._resolve_value(arg) == "count-42"

    def test_unregistered_variable_raises(self):
        arg = _ref('$acme.files.:name("{@missing}")').parsed.name_one.path[0].arg
        with pytest.raises(Exception):
            _dummy()._resolve_value(arg)

    def test_set_variable_after_construction(self):
        arg = _ref('$acme.files.:name("{@company}")').parsed.name_one.path[0].arg
        finder = _dummy()
        finder.set_variable("company", value="acme-corp")
        assert finder._resolve_value(arg) == "acme-corp"

    def test_set_variables_bulk_merges_with_existing(self):
        arg = _ref('$acme.files.:name("{@a}-{@b}")').parsed.name_one.path[0].arg
        finder = _dummy({"a": "1"})
        finder.set_variables({"b": "2"})
        assert finder._resolve_value(arg) == "1-2"

    def test_bare_variable_resolves_to_its_raw_registered_value(self):
        # added 2026-08-27 -- unlike the interpolation-part case above,
        # a BARE Variable3 (not embedded in "{...}") returns the raw
        # value, not a stringified one -- a direct function argument
        # (e.g. :having(@id)) may need to stay whatever type it really
        # is, not become text.
        finder = _dummy({"n": 42})
        assert finder._resolve_value(Variable3(name="n")) == 42

    def test_bare_unregistered_variable_raises_runtime_exception(self):
        with pytest.raises(ReferenceRuntimeException3):
            _dummy()._resolve_value(Variable3(name="missing"))


class TestBuildAndResolveArg:
    # central, eager arg resolution (settled 2026-08-27, David: "central
    # eager resolve of args is right, certainly for now, at least") --
    # _build()/_build_chain() wrap ReferenceFunctionFactory.build()/
    # build_chain(), resolving a Variable3/InterpolatedString3 arg in
    # place so every other call site in every finder just reads .arg
    # and gets a plain, already-resolved value.
    def test_build_resolves_a_registered_variable_arg(self):
        finder = _dummy({"id": "orders"})
        call = FunctionCall3(name="having", arg=Variable3(name="id"))
        built = finder._build(call)
        assert built.arg == "orders"

    def test_build_leaves_a_plain_arg_unchanged(self):
        finder = _dummy()
        call = FunctionCall3(name="having", arg="orders")
        built = finder._build(call)
        assert built.arg == "orders"

    def test_build_raises_runtime_exception_for_unregistered_variable(self):
        finder = _dummy()
        call = FunctionCall3(name="having", arg=Variable3(name="id"))
        with pytest.raises(ReferenceRuntimeException3):
            finder._build(call)

    def test_build_raises_runtime_exception_for_wrong_resolved_type(self):
        # :having() takes (str,) -- a variable that resolves to an int
        # passes check_valid()'s own structural check (Variable3 is
        # unconditionally allowed there, regardless of ARG_TYPES) but
        # fails here, once the real value is actually known.
        finder = _dummy({"id": 5})
        call = FunctionCall3(name="having", arg=Variable3(name="id"))
        with pytest.raises(ReferenceRuntimeException3):
            finder._build(call)

    def test_build_chain_resolves_every_functions_own_arg(self):
        finder = _dummy({"id": "orders"})
        calls = [FunctionCall3(name="having", arg=Variable3(name="id"))]
        built = finder._build_chain(calls)
        assert built[0].arg == "orders"

    def test_nested_function_arg_is_also_resolved(self):
        # :errors(:idchain(@pattern))-style nesting -- ReferenceFunctionFactory.
        # build() already recurses to compile the inner FunctionCall3
        # into a real Function3 before the outer one is constructed;
        # _resolve_arg() must recurse the same way to reach the INNER
        # function's own arg, not just the outer one.
        finder = _dummy({"pattern": "add[0]"})
        inner = FunctionCall3(name="idchain", arg=Variable3(name="pattern"))
        outer = FunctionCall3(name="errors", arg=inner)
        built = finder._build(outer)
        assert built.arg.arg == "add[0]"
