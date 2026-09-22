"""Encodes the currently-buildable RESULTS examples from
`references_notes/notes/normative_reference_examples.txt` as real, running
assertions -- David's own agreed alternative to relying on manual code
review against the doc: "rely on...the normative references" instead.

Scope, deliberately narrow: RESULTS only, for now -- FILES/CSVPATHS get
their own normative test files once their own doc sections are reviewed
the same way this one was (2026-08-11). Within RESULTS, only examples using
functions/mechanisms that are actually built today are included, per the
doc's own note ("all functions may not be available at v3 launch"); each
test below is commented with the exact doc line it encodes. When the doc
gains new supported examples, or a currently-excluded one becomes
supported, add/move the corresponding test here -- this file is meant to
grow in lockstep with the doc, not be written once and left behind.

Excluded doc lines and why (checked directly against the doc as of
2026-08-12, not assumed):
  - line 39 (:groups()) -- built 2026-08-12 (was excluded/deferred as of
    this file's original writing); see TestFindingTheLastRun.
  - lines 42/48/51 (:from()/:yesterday()/:hour()/:message()/:count()/
    :above()) -- none of these functions are built yet. Lines 42/51 also
    use a bare '*' in name_three, which is illegal (see
    references_v3_compendium.md's "Why `*` is disallowed as name_three's
    body").
  - lines 69/72/75/78 (:name() with a regex/star/@var argument, :choice(),
    :type()) -- Name3 is str-arg only today; :choice()/:type() do not
    exist yet.
  - lines 96-111 (:from(), :date(), :year(), :type()) -- none built yet.

The `.:all():data()` example (which raised, since Rule 1 forbids combining
':all()' with any content accessor) was removed from the doc entirely; no
corresponding test lives here for it.

REVISED 2026-09-21: an earlier version of this docstring (and this file's
own fixtures) treated bare '*'/':all()' as one-level operators, peers of
each other but distinct from a bare pointer's zero-level meaning -- settled
2026-08-11, predating this review arc's compendium/normative-doc work. That
is now superseded: per compendium 4.2b, ':all()' (and an explicit trailing
'*') degenerate to the run_dir slot's own zero-level meaning whenever
nothing else occupies that position, regardless of what literal prefix
precedes them -- a bare pointer, a bare '*', and a bare ':all()' are all
equivalent, and so are "beta/*" and "beta/:all()". See
results_reference_finder_3.py's own 2026-09-21 revision notes for the
implementation-side fix this test file was rewritten to match.
"""

import json

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3


class _FakeConfig:
    def __init__(self, archive: str):
        self._archive = archive

    def get(self, *, section, name):
        assert (section, name) == ("results", "archive")
        return self._archive


class _FakeResultsManager:
    def __init__(self, archive: str):
        self._archive = archive

    def get_named_results_home(self, name):
        import os

        return os.path.join(self._archive, name)

    @property
    def results_root_manifest(self):
        with open(f"{self._archive}/manifest.json") as f:
            return json.load(f)


class _FakeCsvPaths:
    def __init__(self, archive: str):
        self.results_manager = _FakeResultsManager(archive)
        self.config = _FakeConfig(archive)


def _write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _make_run(base, run_name: str, run_uuid: str, instances: dict) -> str:
    """instances: {identity: instance_uuid}. Returns the run's own full
    path (for use as a "run_home" entry in the fake archive manifest)."""
    run_dir = base / run_name
    _write_json(run_dir / "manifest.json", {"run_uuid": run_uuid})
    for identity, inst_uuid in instances.items():
        _write_json(run_dir / identity / "manifest.json", {"uuid": inst_uuid})
    return str(run_dir)


def _write_archive_manifest(archive, group: str, run_homes: list) -> None:
    entries = [{"named_paths_name": group, "run_home": rh} for rh in run_homes]
    _write_json(archive / "manifest.json", entries)


def _finder(reference: str, archive: str) -> ResultsReferenceFinder3:
    csvpaths = _FakeCsvPaths(archive)
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return ResultsReferenceFinder3(csvpaths=csvpaths, ref=ref)


class TestFindingTheLastRun:
    # doc lines 30-38: "Finding the 'last' run or runs of a type of
    # information" -- REVISED 2026-09-21, alongside the finder's own
    # zero-level/degenerate-grouping fix (compendium 4.2b: ':all()'/'*'
    # degenerate to zero-level whenever they occupy the run_dir slot,
    # regardless of what literal prefix precedes them). Two runs at
    # each depth the doc's examples need -- no template ("flat"), one
    # 1-level template ("zero/"), and one 1-level template under an
    # explicit literal prefix ("beta/") -- so each test can prove
    # pooling/degeneracy picks the true latest, not just the only one.
    @pytest.fixture
    def alpha_archive(self, tmp_path):
        base = tmp_path / "alpha"
        flat1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        flat2 = _make_run(base, "2026-01-02_00-00-00", "flat-2", {})
        zero1 = _make_run(base / "zero", "2026-01-03_00-00-00", "zero-1", {})
        zero2 = _make_run(base / "zero", "2026-01-04_00-00-00", "zero-2", {})
        beta1 = _make_run(base / "beta", "2026-01-05_00-00-00", "beta-1", {})
        beta2 = _make_run(base / "beta", "2026-01-06_00-00-00", "beta-2", {})
        _write_archive_manifest(
            tmp_path, "alpha", [flat1, flat2, zero1, zero2, beta1, beta2]
        )
        return str(tmp_path)

    def test_line_30_bare_pointer_is_zero_level(self, alpha_archive):
        # $alpha.results.:last() >> run with no template
        results = _finder("$alpha.results.:last()", alpha_archive).query()
        assert results.uuids == ["flat-2"]

    def test_line_31_star_is_zero_level_same_as_bare_pointer(self, alpha_archive):
        # $alpha.results.*:last() >> run with no template, same as
        # without the wildcard -- REVISED 2026-09-21 (was "one level"):
        # a bare '*' represents the run_dir slot itself, same as a bare
        # pointer alone.
        results = _finder("$alpha.results.*:last()", alpha_archive).query()
        assert results.uuids == ["flat-2"]

    def test_line_32_all_is_zero_level_degenerate_same_as_bare_pointer(
        self, alpha_archive
    ):
        # $alpha.results.:all():last() >> run with no template, same as
        # with the wildcard -- REVISED 2026-09-21 (was: groups by
        # whatever 1-level templates happen to exist). Per compendium
        # 4.2b, ':all()' at the run_dir slot degenerates to '*' -- there
        # is nothing to group by, since run_dir names never repeat --
        # so this gives the single true latest zero-level run, same as
        # lines 30/31, not one result per template.
        results = _finder("$alpha.results.:all():last()", alpha_archive).query()
        assert results.uuids == ["flat-2"]

    def test_line_33_flatten_pools_any_depth(self, alpha_archive):
        # $alpha.results.:flatten():last() >> run (single, any depth)
        # beta-2 is the true chronological latest across every depth.
        results = _finder("$alpha.results.:flatten():last()", alpha_archive).query()
        assert results.uuids == ["beta-2"]

    def test_line_34_prefixed_flatten_any_depth_beyond_prefix(self, alpha_archive):
        # $alpha.results.beta/:flatten():last() >> run of all templates
        # starting `beta`
        results = _finder(
            "$alpha.results.beta/:flatten():last()", alpha_archive
        ).query()
        assert results.uuids == ["beta-2"]

    def test_line_35_prefixed_all_degenerates_same_as_prefixed_star(
        self, alpha_archive
    ):
        # $alpha.results.beta/:all():last() >> last run of all 1-level
        # templates starting `beta/` -- REVISED 2026-09-21 (was: groups
        # by a 2nd template level beyond "beta"). ':all()' here still
        # sits at the run_dir slot (the fixed "beta/" prefix does not
        # change that), so this degenerates to the exact same candidate
        # set "beta/*" gives -- a single pooled result, not one per run.
        results = _finder(
            "$alpha.results.beta/:all():last()", alpha_archive
        ).query()
        assert results.uuids == ["beta-2"]

    def test_line_36_prefixed_star_pools_same_level(self, alpha_archive):
        # $alpha.results.beta/*:last() >> a run of all 1-level templates
        # starting `beta/` -- single, pooled, identical result to line
        # 35 (the doc's own point: these two are deliberately
        # equivalent, per the "better written as" note next to
        # ':all()').
        results = _finder("$alpha.results.beta/*:last()", alpha_archive).query()
        assert results.uuids == ["beta-2"]

    def test_line_37_manifest_at_literal_root_is_zero_level(self, alpha_archive):
        # $alpha.results.:manifest():last() >> manifest entry of the
        # most recent run with no template
        results = _finder(
            "$alpha.results.:manifest():last()", alpha_archive
        ).resolve()
        assert results.results[0].data["run_uuid"] == "flat-2"

    def test_line_38_global_manifest_is_unrestricted(self, tmp_path):
        # $*.results.:manifest():last() >> manifest entry of the most
        # recent run, period -- reads the archive-wide ledger directly,
        # bypassing the zero-level restriction entirely (Rule 1b is
        # checked before the zero-level logic ever runs). The archive
        # ledger's own entries carry "run_uuid" (not "uuid"), unlike
        # alpha_archive's fixture -- a dedicated, minimal ledger is used
        # here rather than _write_archive_manifest, same as the ordinal-
        # indexing tests in test_results_reference_finder_3.py.
        ledger = [
            {"named_paths_name": "alpha", "run_uuid": "run-1"},
            {"named_paths_name": "alpha", "run_uuid": "run-2"},
        ]
        _write_json(tmp_path / "manifest.json", ledger)
        results = _finder("$*.results.:manifest():last()", str(tmp_path)).resolve()
        assert results.results[0].data["run_uuid"] == "run-2"

    def test_line_39_groups_reaches_every_template_and_non_template_run_dir(
        self, alpha_archive
    ):
        # $alpha.results.:groups():last() >> runs for every template and
        # non-template run dir -- unaffected by the 2026-09-21 ':all()'
        # fix (':groups()' already correctly excluded the run's own
        # trailing name from its group key). alpha_archive has three
        # distinct groups (zero-level, "zero", "beta"), two runs each,
        # so ':last()' of each group is that group's own later run.
        results = _finder("$alpha.results.:groups():last()", alpha_archive).query()
        assert set(results.uuids) == {"flat-2", "zero-2", "beta-2"}


class TestAllIsAZeroLevelDegenerateOperator:
    # doc line 54: $acme.results.:all() >> every run having no template,
    # same as bare '*' -- REVISED 2026-09-21 (was "one-level operator,
    # peer of '*'", settled 2026-08-11; superseded now that '*'/':all()'
    # both degenerate to the run_dir slot per compendium 4.2b). With no
    # pointer, every zero-level run comes back unreduced -- the
    # customers/customers-2025 runs (1- and 2-level) are excluded, same
    # as they would be for a bare pointer or bare '*'.
    def test_line_54_all_with_no_pointer_is_zero_level_unreduced(self, tmp_path):
        base = tmp_path / "acme"
        flat1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        flat2 = _make_run(base, "2026-01-02_00-00-00", "flat-2", {})
        one_level = _make_run(base / "customers", "2026-01-03_00-00-00", "one-uuid", {})
        two_level = _make_run(
            base / "customers" / "2025", "2026-01-04_00-00-00", "two-uuid", {}
        )
        _write_archive_manifest(
            tmp_path, "acme", [flat1, flat2, one_level, two_level]
        )
        results = _finder("$acme.results.:all()", str(tmp_path)).query()
        assert set(results.uuids) == {"flat-1", "flat-2"}


class TestPathNarrowingAndInstanceSelection:
    # doc lines 57-90: literal/wildcard path narrowing down to a run,
    # then a literal statement identity ("invoices") and its well-known
    # output files.
    @pytest.fixture
    def acme_archive(self, tmp_path):
        base = tmp_path / "acme"
        cust2025_1 = _make_run(
            base / "customers" / "2025",
            "2026-01-01_00-00-00",
            "cust2025-1-uuid",
            {"invoices": "invoices-1-uuid"},
        )
        cust2025_2 = _make_run(
            base / "customers" / "2025",
            "2026-01-02_00-00-00",
            "cust2025-2-uuid",
            {"invoices": "invoices-2-uuid"},
        )
        region2025 = _make_run(
            base / "region" / "office" / "2025",
            "2026-01-03_00-00-00",
            "region2025-uuid",
            {"invoices": "invoices-region-uuid"},
        )
        one_level_customers = _make_run(
            base / "customers", "2026-01-04_00-00-00", "one-level-uuid", {}
        )
        _write_archive_manifest(
            tmp_path,
            "acme",
            [cust2025_1, cust2025_2, region2025, one_level_customers],
        )
        return str(tmp_path)

    def test_line_57_literal_two_level_path(self, acme_archive):
        # $acme.results.customers/2025:first() >> first run with
        # template customers/2025
        results = _finder(
            "$acme.results.customers/2025:first()", acme_archive
        ).query()
        assert results.uuids == ["cust2025-1-uuid"]

    def test_line_60_identity_lookup_on_the_selected_run(self, acme_archive):
        # $acme.results.customers/2025:first().invoices
        results = _finder(
            "$acme.results.customers/2025:first().invoices", acme_archive
        ).query()
        assert results.uuids == ["invoices-1-uuid"]

    def test_line_63_wildcard_prefix_ending_in_a_literal(self, acme_archive):
        # $acme.results.*/2025:first().invoices >> ending `2025`,
        # 2-level only -- matches customers/2025, not region/office/2025.
        results = _finder(
            "$acme.results.*/2025:first().invoices", acme_archive
        ).query()
        assert results.uuids == ["invoices-1-uuid"]

    def test_line_66_two_wildcards_ending_in_a_literal(self, acme_archive):
        # $acme.results.*/*/2025:first().invoices >> 3-level ending
        # `2025` -- matches region/office/2025, not customers/2025.
        results = _finder(
            "$acme.results.*/*/2025:first().invoices", acme_archive
        ).query()
        assert results.uuids == ["invoices-region-uuid"]

    def test_line_81_file_accessor_on_a_wildcard_matched_instance(
        self, acme_archive
    ):
        # $acme.results.*/2025:first().invoices:file("report.txt")
        import os

        instance_dir = os.path.join(
            acme_archive, "acme", "customers", "2025", "2026-01-01_00-00-00", "invoices"
        )
        os.makedirs(instance_dir, exist_ok=True)
        with open(os.path.join(instance_dir, "report.txt"), "w") as f:
            f.write("report content")
        results = _finder(
            '$acme.results.*/2025:first().invoices:file("report.txt")',
            acme_archive,
        ).resolve()
        assert results.results[0].data == b"report content"

    def test_line_84_data_accessor(self, acme_archive):
        # $acme.results.customers/2025:first().invoices:data()
        import os

        instance_dir = os.path.join(
            acme_archive, "acme", "customers", "2025", "2026-01-01_00-00-00", "invoices"
        )
        os.makedirs(instance_dir, exist_ok=True)
        with open(os.path.join(instance_dir, "data.csv"), "wb") as f:
            f.write(b"a,b\n1,2\n")
        results = _finder(
            "$acme.results.customers/2025:first().invoices:data()", acme_archive
        ).resolve()
        assert results.results[0].data == b"a,b\n1,2\n"

    def test_line_87_vars_accessor(self, acme_archive):
        # $acme.results.customers/2025:first().invoices:vars()
        import os

        instance_dir = os.path.join(
            acme_archive, "acme", "customers", "2025", "2026-01-01_00-00-00", "invoices"
        )
        os.makedirs(instance_dir, exist_ok=True)
        with open(os.path.join(instance_dir, "vars.json"), "w") as f:
            json.dump({"count": 3}, f)
        results = _finder(
            "$acme.results.customers/2025:first().invoices:vars()", acme_archive
        ).resolve()
        assert results.results[0].data == {"count": 3}

    def test_line_90_meta_accessor(self, acme_archive):
        # $acme.results.customers/2025:first().invoices:meta()
        import os

        instance_dir = os.path.join(
            acme_archive, "acme", "customers", "2025", "2026-01-01_00-00-00", "invoices"
        )
        os.makedirs(instance_dir, exist_ok=True)
        with open(os.path.join(instance_dir, "meta.json"), "w") as f:
            json.dump({"identity": "invoices"}, f)
        results = _finder(
            "$acme.results.customers/2025:first().invoices:meta()", acme_archive
        ).resolve()
        assert results.results[0].data == {"identity": "invoices"}

    def test_line_114_manifest_before_pointer_at_a_one_level_template(
        self, acme_archive
    ):
        # $acme.results.customers:manifest():first() >> manifest of
        # first run with 1-level template `customers`
        results = _finder(
            "$acme.results.customers:manifest():first()", acme_archive
        ).resolve()
        assert results.results[0].data["run_uuid"] == "one-level-uuid"

    def test_line_117_pointer_before_manifest_same_result(self, acme_archive):
        # $acme.results.customers:first():manifest() -- same as line
        # 114, order does not matter.
        results = _finder(
            "$acme.results.customers:first():manifest()", acme_archive
        ).resolve()
        assert results.results[0].data["run_uuid"] == "one-level-uuid"


class TestHomeAsAZeroLevelSelector:
    # decided jointly 2026-08-11, added to the doc under its own new
    # "## :home() as a zero-level selector" heading -- fills the one
    # real gap in the depth model: no existing mechanism returned
    # "every zero-level run, unreduced" (bare pointer always reduces to
    # one; ':all()' is one-level not zero; ':flatten()' is any depth
    # not zero). Works because ':home()' is VALUE-role, never a
    # POINTER -- when it is the only function present, nothing reduces
    # the candidate set.
    def test_bare_home_lists_every_no_template_run(self, tmp_path):
        base = tmp_path / "alpha"
        flat1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        flat2 = _make_run(base, "2026-01-02_00-00-00", "flat-2", {})
        one_level = _make_run(
            base / "zero", "2026-01-03_00-00-00", "one-level", {}
        )
        _write_archive_manifest(tmp_path, "alpha", [flat1, flat2, one_level])
        results = _finder("$alpha.results.:home()", str(tmp_path)).query()
        assert set(results.uuids) == {"flat-1", "flat-2"}

    def test_home_then_pointer_order_independent(self, tmp_path):
        base = tmp_path / "alpha"
        flat1 = _make_run(base, "2026-01-01_00-00-00", "flat-1", {})
        flat2 = _make_run(base, "2026-01-02_00-00-00", "flat-2", {})
        _write_archive_manifest(tmp_path, "alpha", [flat1, flat2])
        home_first = _finder(
            "$alpha.results.:home():last()", str(tmp_path)
        ).query()
        pointer_first = _finder(
            "$alpha.results.:last():home()", str(tmp_path)
        ).query()
        assert home_first.uuids == pointer_first.uuids == ["flat-2"]

    # NOTE: there is no prefixed equivalent ("beta/:home()") -- a plain
    # literal prefix with nothing trailing already means "every run
    # under this exact prefix, unreduced" (confirmed identical results
    # in every case tested), so ':home()' is root-only.
    def test_prefixed_home_is_not_a_thing_use_the_literal_prefix_alone(
        self, tmp_path
    ):
        base = tmp_path / "acme"
        beta1 = _make_run(base / "beta", "2026-01-01_00-00-00", "beta-1", {})
        beta2 = _make_run(base / "beta", "2026-01-02_00-00-00", "beta-2", {})
        _write_archive_manifest(tmp_path, "acme", [beta1, beta2])
        plain_prefix = _finder("$acme.results.beta", str(tmp_path)).query()
        assert set(plain_prefix.uuids) == {"beta-1", "beta-2"}
        with pytest.raises(ReferenceException3):
            _finder("$acme.results.beta/:home()", str(tmp_path)).query()
