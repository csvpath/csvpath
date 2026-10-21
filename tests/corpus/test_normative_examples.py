"""Validates normative reference-v3 expressions (see
specs/references_v3/spec/normative_reference_examples.txt) against the real,
committed corpus under tests/corpus/data/ -- a different layer than the
existing tests/references/ unit tests, which exercise FilesReferenceFinder3/
ResultsReferenceFinder3/CsvpathsReferenceFinder3 against hand-built, synthetic
manifest fixtures. Here the data comes from real FileManager/PathsManager/
CsvPaths.fast_forward_paths() calls (see tests/corpus/generate.py), so a
passing test here proves the finder's expectations about manifest/directory
shape actually match what production registration/run code writes, not just
what a test author assumed it would.

This is a representative first pass, not a line-by-line transcription of
every example in the normative doc -- it covers one or two concrete,
corpus-backed cases per major construct family (before/after/to/from,
:groups() range semantics, the field accessor taxonomy, root_major functions,
depth-matrix gotchas). Extend it as the corpus grows.

Deliberately NOT covered here: bare time-window functions (:yesterday(),
:today(), :now(), etc.) and :date()-literal comparisons. Those depend on
wall-clock "now" at TEST-RUN time, but this module queries the COMMITTED
snapshot, whose absolute timestamps were fixed relative to whenever
generate.py last ran -- asserting on them here would silently go stale as
the snapshot ages. A future pass should add a separate fixture that
regenerates a small, throwaway corpus fresh (under tmp_path) for exactly
those cases.
"""
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3

CORPUS_CONFIG = os.path.join(os.path.dirname(__file__), "config", "config.ini")


@pytest.fixture(scope="module")
def csvpaths():
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = CORPUS_CONFIG
    try:
        yield CsvPaths()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _query(csvpaths, cls, reference: str):
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    finder = cls(csvpaths=csvpaths, ref=ref)
    return finder.query()


class TestBeforeAfterToFrom:
    """normative doc, 'Before and after, from and to' -- index-based, so
    stable across regenerations regardless of calendar drift."""

    def test_groups_from_to_first_two_versions(self, csvpaths):
        # orders has 5 distinct registered versions (see assets.yaml) --
        # :groups() reduces per-partition (PR #431), so :from(0):to(1)
        # selects the first two, oldest-first.
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.:groups().:from(0):to(1)")
        assert len(r.files) == 2
        assert r.files[0].endswith("74d3787c36bdb2098a3479126d28970618696237d63f9006717d61e86af5a988.csv")
        assert r.files[1].endswith("084f52949fe0952c2ad5bc4629f300e1f7dad4c9127fa96c3a701a34229c2f3b.csv")

    def test_groups_before_index(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.:groups().:before(:index(1))")
        assert len(r.files) == 1
        assert r.files[0].endswith("74d3787c36bdb2098a3479126d28970618696237d63f9006717d61e86af5a988.csv")

    def test_groups_after_index(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.:groups().:after(:index(3))")
        assert len(r.files) == 1
        assert r.files[0].endswith("baf45aae8cbdb1de423d10e9f81f689f417ee21b29ee88bf95ce71600ae2aa44.csv")

    def test_csvpaths_before_after_index(self, csvpaths):
        # validate_orders has 3 versions (1 initial load + 2 real
        # add_named_paths(append=True) accumulations, see assets.yaml).
        before = _query(csvpaths, CsvpathsReferenceFinder3, "$validate_orders.csvpaths.:before(:index(2))")
        after = _query(csvpaths, CsvpathsReferenceFinder3, "$validate_orders.csvpaths.:after(:index(0))")
        assert len(before.files) == 2
        assert len(after.files) == 2

    def test_results_flatten_before_after_index(self, csvpaths):
        # validate_orders has 6 runs (assets.yaml).
        before = _query(
            csvpaths, ResultsReferenceFinder3,
            "$validate_orders.results.:flatten():before(:index(2))",
        )
        after = _query(
            csvpaths, ResultsReferenceFinder3,
            "$validate_orders.results.:flatten():after(:index(2))",
        )
        assert len(before.files) == 2
        assert len(after.files) == 3

    def test_results_error_count_range_generator(self, csvpaths):
        # normative doc: "Two ways of selecting runs without errors" --
        # every run in the corpus is error-free (the deliberately
        # failing "candy check" statement's own threshold is never
        # actually tripped by food.csv), so both forms should agree and
        # cover all 11 runs across every named-paths group.
        below = _query(
            csvpaths, ResultsReferenceFinder3,
            "$*.results.:flatten():error_count(:below(1))",
        )
        literal_zero = _query(
            csvpaths, ResultsReferenceFinder3,
            "$*.results.:flatten():error_count(0)",
        )
        above = _query(
            csvpaths, ResultsReferenceFinder3,
            "$*.results.:flatten():error_count(:above(0))",
        )
        assert len(below.files) == 11
        assert len(literal_zero.files) == 11
        assert above.files == []


class TestFieldAccessorTaxonomy:
    """normative doc, 'The field accessor functional taxonomy' -- Names,
    Fingerprint, Type sections."""

    def test_type_selects_xlsx(self, csvpaths):
        r = _query(
            csvpaths, FilesReferenceFinder3,
            '$energy_readings.files.:flatten():type("xlsx")',
        )
        assert r.files == ["tests/corpus/data/inputs/named_files/energy_readings/Book1.xlsx"]

    def test_named_file_name_selects_runs(self, csvpaths):
        # normative doc section intro: "Select the first run for each
        # template for runs having the named-file name orders" --
        # exercised here as a plain name filter (no :groups()/:first()
        # chained) since only one named-paths group (validate_orders)
        # runs against orders in this corpus.
        r = _query(
            csvpaths, ResultsReferenceFinder3,
            '$*.results.:flatten():named_file_name("orders")',
        )
        assert len(r.files) == 6
        r2 = _query(
            csvpaths, ResultsReferenceFinder3,
            '$*.results.:flatten():named_file_name("zipcodes")',
        )
        assert len(r2.files) == 2


class TestRootMajorFunctions:
    """normative doc, 'Functions in root_major' -- :regex()/:choice()."""

    def test_regex_matches_by_name_prefix(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$:regex(/^o/).files.:flatten()")
        assert r.files == ["tests/corpus/data/inputs/named_files/orders/orders/food.csv"]

    def test_choice_matches_named_alternatives(self, csvpaths):
        r = _query(
            csvpaths, FilesReferenceFinder3,
            '$:choice("orders|zipcodes").files.:flatten()',
        )
        assert sorted(r.files) == sorted(
            [
                "tests/corpus/data/inputs/named_files/zipcodes/zipcodes.csv",
                "tests/corpus/data/inputs/named_files/orders/orders/food.csv",
            ]
        )


class TestDefinitionFiles:
    """normative doc, 'Definition files'."""

    def test_bare_definition_returns_path(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.:definition()")
        assert r.files == ["tests/corpus/data/inputs/named_files/orders/definition.json"]


class TestPointerDepthMatrix:
    """normative doc + files_reference_finder_3.py's own _query_star_
    traversal() docstring: bare '*' (as name_one, after a literal
    root_major) pools EXACTLY one level; ':all()' groups one level;
    ':flatten()'/':groups()' are the any-depth POOL/GROUP peers. `orders`
    uses a 1-level template ("orders/:filename"), so its real file_home
    ("orders/food.csv") is two segments deep -- a genuine, documented
    depth mismatch a one-level '*'/bare pointer cannot reach, exactly the
    scenario the depth matrix exists to handle via :flatten()/:groups()
    instead. Kept as its own test class because this is a real gotcha
    worth a subagent/human understanding explicitly, not just an
    implementation detail."""

    def test_bare_pointer_misses_templated_depth(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.:last()")
        assert r.files == []

    def test_star_one_level_pool_misses_templated_depth(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.*.:last()")
        assert r.files == []

    def test_literal_path_prefix_reaches_templated_depth(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.orders/:last()")
        assert len(r.files) == 1
        assert r.files[0].endswith("baf45aae8cbdb1de423d10e9f81f689f417ee21b29ee88bf95ce71600ae2aa44.csv")

    def test_groups_any_depth_reaches_templated_depth(self, csvpaths):
        # :groups() is the any-depth GROUP peer -- reaches orders/food.csv
        # despite the template, unlike bare '*' above.
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.:groups()")
        assert r.files == ["tests/corpus/data/inputs/named_files/orders/orders/food.csv"]

    def test_star_one_level_pool_reaches_flat_group(self, csvpaths):
        # acme_invoices has no template -- its file_homes sit directly
        # under the name home, exactly one level deep, so '*' (the
        # one-level POOL) reaches them fine.
        r = _query(csvpaths, FilesReferenceFinder3, "$acme_invoices.files.*.:last()")
        assert len(r.files) == 1


class TestOnePointerPerReference:
    """normative doc, 'Pointers' -- 'Two pointers can not cohabitate the
    same reference in the same context.'"""

    def test_two_pointers_in_one_context_rejected(self, csvpaths):
        with pytest.raises(ReferenceException3):
            _query(csvpaths, FilesReferenceFinder3, "$orders.files.:first():last()")


class TestTemplatePredicateFiltering:
    """FilesReferenceFinder3.query()'s literal-root bare_field_call branch
    previously returned definition.json unconditionally for ANY
    ':template(...)' call, ignoring the argument entirely -- confirmed
    live, :template(:empty()) and :template(:not_empty()) both matched
    every named-file regardless of its actual template value. Fixed
    2026-10-21, two changes:
    - Template3.ARG_TYPES widened from () to (PredicateFunction3,),
      mirroring OnArrival3's own identical widening -- the argument was
      being rejected by _build() before query() ever got a chance to
      apply it.
    - query()'s bare_field_call branch now calls the existing, already-
      generic _matches_definition_field_predicate() (built for
      ':on_arrival()' nested inside ':definition(...)' during '*'
      traversal) when an argument is present, instead of ignoring it.

    Neither `orders` nor `zipcodes` has ever set a DEFAULT template via
    a dedicated call -- per David, a named-file's definition.json
    intentionally does NOT store a default merely because some
    individual add_named_file() registration happened to pass a
    template (unlike named-paths, where the add-time template IS the
    assumed default for future runs). So both groups' real `template`
    value is None, and :not_empty() correctly matches both (None != ""),
    while :empty() matches neither (None != "") -- :empty()/:not_empty()
    distinguish from a literal empty string, not from a missing/None
    value (that's :none()'s own, separate job per the compendium's
    empty/none table) -- confirmed this is consistent with Empty3/
    NotEmpty3's own existing, unmodified implementation.
    """

    def test_not_empty_matches_named_files_with_no_default_template(self, csvpaths):
        for name in ("zipcodes", "orders"):
            r = _query(csvpaths, FilesReferenceFinder3, f"${name}.files.:template(:not_empty())")
            assert r.files == [f"tests/corpus/data/inputs/named_files/{name}/definition.json"]

    def test_empty_matches_neither_since_value_is_none_not_empty_string(self, csvpaths):
        for name in ("zipcodes", "orders"):
            r = _query(csvpaths, FilesReferenceFinder3, f"${name}.files.:template(:empty())")
            assert r.files == []

    def test_bare_template_still_unaffected(self, csvpaths):
        # no argument at all -- the ordinary bare read, confirmed
        # unaffected by the predicate-filtering addition.
        r = _query(csvpaths, FilesReferenceFinder3, "$orders.files.:template()")
        assert r.files == ["tests/corpus/data/inputs/named_files/orders/definition.json"]

    def test_literal_string_argument_still_rejected(self, csvpaths):
        # Template3.ARG_TYPES only widened to accept a PredicateFunction3
        # (matching OnArrival3's own precedent exactly) -- a raw literal
        # is not one of the "select by literal match" functional-taxonomy
        # fields (uuid/name/fingerprint/type), so this stays rejected,
        # not silently accepted.
        with pytest.raises(ReferenceException3):
            _query(csvpaths, FilesReferenceFinder3, '$orders.files.:template("orders/:filename")')


class TestStatusRegistrationFailed:
    """FilesReferenceFinder3._ledger_entry_result_path() raises
    ReferenceException3 for a 'Registration failed' ledger entry whose
    origin_path is the empty string -- the one input confirmed (by the
    real test_file_registration_failed test) to actually produce this
    status can never be reported back through
    :status("Registration failed"). Flagged to David, not yet fixed on
    this branch (tracked separately -- see PR #434)."""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "FilesReferenceFinder3._ledger_entry_result_path() raises "
            "ReferenceException3 for a 'Registration failed' ledger entry "
            "whose origin_path is the empty string -- fix tracked in a "
            "separate PR (#434), not this branch."
        ),
    )
    def test_status_registration_failed_is_selectable(self, csvpaths):
        r = _query(
            csvpaths, FilesReferenceFinder3,
            '$orders.files.:status("Registration failed")',
        )
        assert len(r.files) == 1


class TestStarTemplatePredicateFiltering:
    """FilesReferenceFinder3.query()'s Star3 root_major branch previously
    raised ReferenceException3('Does not yet support :template() as a
    name_one path segment') for the EXACT normative example
    '$*.files.:template(:not_empty())' (normative_reference_examples.txt
    line 197, "get a list of all templates used in registrations") --
    a known, cleanly-rejected gap, not silently wrong, but it still
    blocked this normative example from working at all. Fixed 2026-10-21:
    _query_star_traversal() now recognizes a bare BARE_SOURCE ==
    "definition" field call (the same _bare_definition_field_call()
    check the literal-root branch uses) and applies the identical
    predicate-filtering logic across every matching named-file, instead
    of falling through to generic path-pattern compilation."""

    def test_not_empty_matches_every_named_file_with_no_default_template(self, csvpaths):
        # none of the four named-files groups has ever set a default
        # template via a dedicated call (see TestTemplatePredicateFiltering
        # above) -- :not_empty() correctly matches all of them (None != "").
        r = _query(csvpaths, FilesReferenceFinder3, "$*.files.:template(:not_empty())")
        assert sorted(r.files) == sorted(
            f"tests/corpus/data/inputs/named_files/{name}/definition.json"
            for name in ("acme_invoices", "orders", "zipcodes", "energy_readings")
        )

    def test_empty_matches_none(self, csvpaths):
        r = _query(csvpaths, FilesReferenceFinder3, "$*.files.:template(:empty())")
        assert r.files == []

    def test_name_three_still_rejected(self, csvpaths):
        # definition.json is never versioned -- same restriction as the
        # literal-root branch and as bare ':definition()' itself.
        with pytest.raises(ReferenceException3):
            _query(csvpaths, FilesReferenceFinder3, "$*.files.:template(:not_empty()).:first()")
