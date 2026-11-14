import pytest

from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from csvpath.references.reference_3 import Star3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.reference_results_3 import ReferenceResult3
from csvpath.util.path_util import PathUtility as pathu


#
# fixture: named-paths group "acme" with two loaded versions. version 0
# has two statements (one identified as "company_names", one unnamed --
# unnamed statements get the stringified load-time index as their
# identity, per PathsManager.add_named_paths); version 1 has one
# unnamed statement. group_file_path is identical across every version
# -- there is only one group.csvpath file, ever, regardless of version
# (confirmed against PathsRegistrar.metadata_update's real manifest
# schema).
#
GROUP_FILE_PATH = "named_paths/acme/group.csvpath"
ACME_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v0-uuid",
        "named_paths": ["stmt text A", "stmt text B"],
        "named_paths_identities": ["company_names", "1"],
    },
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v1-uuid",
        "named_paths": ["stmt text C"],
        "named_paths_identities": ["0"],
    },
]


GROUP_HOME = "named_paths/acme"


class _FakePathsDescriber:
    def __init__(self, definition: dict, definitions_by_name: dict | None = None):
        self._definition = definition
        self._definitions_by_name = definitions_by_name

    def get_config(self, name):
        from csvpath.managers.paths.paths_descriptor import GroupConfig

        if self._definitions_by_name is not None:
            return GroupConfig(**self._definitions_by_name[name])
        return GroupConfig(**self._definition)


class _FakePathsManager:
    def __init__(
        self,
        manifest,
        home=GROUP_HOME,
        definition: dict | None = None,
        ledger=None,
        by_name: dict | None = None,
        definitions_by_name: dict | None = None,
    ):
        self._manifest = manifest
        self._home = home
        self._definition = definition or {}
        self._ledger = manifest if ledger is None else ledger
        # by_name: {name: manifest} -- only used by '*' traversal tests,
        # which need more than one distinct named-paths group. Every
        # other test uses the single manifest above.
        self._by_name = by_name
        # definitions_by_name: {name: definition} -- only used by '*'
        # traversal tests for definition.json-backed fields (:scripts()
        # etc), to prove the CORRECT group's own definition is read, not
        # just any -- added 2026-08-18 alongside _group_manifest_entry().
        self._definitions_by_name = definitions_by_name

    def get_manifest_for_name(self, name):
        if self._by_name is not None:
            return self._by_name[name]
        return self._manifest

    def named_paths_home(self, name, *, assure=True):
        # one home per group when there are several, so a definition.json
        # path names its own group (2026-11-10)
        if self._by_name is not None:
            return f"named_paths/{name}"
        return self._home

    @property
    def named_paths_names(self):
        if self._by_name is not None:
            return list(self._by_name.keys())
        return []

    @property
    def paths_root_manifest(self):
        return self._ledger

    @property
    def describer(self):
        return _FakePathsDescriber(self._definition, self._definitions_by_name)


class _FakeConfig:
    def __init__(
        self,
        inputs_csvpaths_path: str | None = None,
        log_file: str | None = None,
    ):
        self.inputs_csvpaths_path = inputs_csvpaths_path
        self.log_file = log_file


class _FakeLogger:
    """captures warning()/etc calls instead of writing anywhere real --
    added 2026-10-18 so tests can assert on the compendium 5.20b
    "last value-producing function wins" warning without needing a
    real csvpaths.logger."""

    def __init__(self):
        self.warnings = []

    def warning(self, msg, *args):
        self.warnings.append(msg % args if args else msg)

    def info(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass


class _FakeCsvPaths:
    def __init__(
        self,
        paths_manager,
        inputs_csvpaths_path: str | None = None,
        log_file: str | None = None,
    ):
        self.paths_manager = paths_manager
        self.config = _FakeConfig(inputs_csvpaths_path, log_file=log_file)
        self.logger = _FakeLogger()


def _finder(
    reference: str,
    manifest: list = ACME_MANIFEST,
    definition: dict | None = None,
    inputs_csvpaths_path: str | None = None,
    ledger: list | None = None,
    by_name: dict | None = None,
    definitions_by_name: dict | None = None,
    log_file: str | None = None,
    variables: dict | None = None,
) -> CsvpathsReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakePathsManager(
            manifest,
            definition=definition,
            ledger=ledger,
            by_name=by_name,
            definitions_by_name=definitions_by_name,
        ),
        inputs_csvpaths_path=inputs_csvpaths_path,
        log_file=log_file,
    )
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref, variables=variables)


class TestVersionPointer:
    def test_last(self):
        results = _finder("$acme.csvpaths.:last()").query()
        assert results.files == [GROUP_FILE_PATH]
        assert results.uuids == ["v1-uuid"]

    def test_first(self):
        results = _finder("$acme.csvpaths.:first()").query()
        assert results.uuids == ["v0-uuid"]

    def test_index(self):
        results = _finder("$acme.csvpaths.:index(0)").query()
        assert results.uuids == ["v0-uuid"]

    def test_index_out_of_range_returns_empty_not_an_error(self):
        results = _finder("$acme.csvpaths.:index(99)").query()
        assert results.files == []

    def test_chained_functions_combine_with_name_ones_own_chain(self):
        # :last() occupies the sole path-segment, :index(0) is name_one's
        # own trailing function chain -- both get combined into one
        # chain; index(0) is the only pointer among the two once
        # combined... except :last() is ALSO a pointer, so this should
        # raise (two pointers, same chain).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:last():index(0)").query()


class TestBareUuidLookup:
    # bare ':uuid("v1-uuid")' -- added 2026-10-18, the compendium's own
    # worked example ("find acme version by UUID; the most specific
    # reference possible"). CSVPATHS never had a bare-lookup shape for
    # ANY function before this -- Fingerprint3's own docstring is
    # explicit that its identical mechanism is FILES-only. Mirrors
    # FilesReferenceFinder3's own TestBareUuidLookup/TestBare
    # FingerprintLookup exactly (same registry-driven
    # SELECTOR_WHEN_ARGUED dispatch/guard, shared code).
    def test_finds_the_matching_version_with_real_path_and_uuid(self):
        results = _finder('$acme.csvpaths.:uuid("v1-uuid")').query()
        assert results.files == [GROUP_FILE_PATH]
        assert results.uuids == ["v1-uuid"]

    def test_no_match_gives_empty(self):
        results = _finder('$acme.csvpaths.:uuid("nope")').query()
        assert results.results == []

    def test_combines_with_name_three(self):
        # not-yet-supported sweep #9, 2026-10-20: the bare selector
        # already reduces to at most one version by construction, so
        # name_three composes safely -- reuses the exact same shared
        # _apply_name_three_to_versions() tail every other selected-
        # versions path in this file goes through. "0" is v1-uuid's own
        # real identity (ACME_MANIFEST above).
        results = _finder('$acme.csvpaths.:uuid("v1-uuid").0').query()
        assert results.uuids == ["v1-uuid"]
        assert results.results[0].identity == "0"

    def test_combined_with_name_three_no_match_gives_empty(self):
        # "company_names" is a real identity, but it belongs to
        # v0-uuid's own version, not v1-uuid's -- confirms the lookup is
        # scoped to the matched version's own identities, not every
        # version's.
        results = _finder('$acme.csvpaths.:uuid("v1-uuid").company_names').query()
        assert results.results == []

    def test_ordinary_field_accessor_usage_is_unaffected(self):
        # riding alongside a pointer in its original, pre-existing job
        # (bare, no arg) still works exactly as before.
        results = _finder("$acme.csvpaths.:last():uuid()").resolve()
        assert results.results[0].data == "v1-uuid"

    # beside a pointer an argued ':uuid()' filters the versions, then the
    # pointer picks, as in RESULTS (David, 2026-11-06; 6.44). It used to
    # raise, which kept the argument from being ignored.
    @pytest.mark.parametrize(
        "reference, expected",
        [
            ('$acme.csvpaths.:last():uuid("v0-uuid")', ["v0-uuid"]),
            ('$acme.csvpaths.:uuid("v0-uuid"):last()', ["v0-uuid"]),
            ('$acme.csvpaths.:first():uuid("v1-uuid")', ["v1-uuid"]),
            ('$acme.csvpaths.:all():uuid("v1-uuid")', ["v1-uuid"]),
            ('$acme.csvpaths.:last():uuid("x")', []),
        ],
    )
    def test_an_argument_beside_a_pointer_filters(self, reference, expected):
        assert _finder(reference).query().uuids == expected

    def test_a_filter_and_a_value_field_together(self):
        results = _finder('$acme.csvpaths.:last():uuid("v0-uuid"):uuid()').resolve()
        assert [r.data for r in results.results] == ["v0-uuid"]


FINGERPRINT_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v0-uuid",
        "named_paths": ["stmt text A", "stmt text B"],
        "named_paths_identities": ["company_names", "1"],
        "fingerprint": "aaaa",
    },
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v1-uuid",
        "named_paths": ["stmt text C"],
        "named_paths_identities": ["0"],
        "fingerprint": "cccc",
    },
]


class TestBareFingerprintLookup:
    # bare ':fingerprint("cccc")' -- settled as an intentional,
    # decided capability 2026-10-18, not just an accidental side
    # effect. An automated cross-datatype consistency sweep found this
    # already worked, live, before anyone had decided it should --
    # CsvpathsReferenceFinder3's own `_is_bare_selector_reference()`
    # dispatch (added for :uuid()'s own build, same day) is generic,
    # keyed on SELECTOR_WHEN_ARGUED, not hardcoded to "uuid," so it
    # picked up :fingerprint() too, for free. Fingerprint3's own
    # docstring used to claim "CSVPATHS has no bare-lookup shape" --
    # David's own call once flagged: keep it (CSVPATHS versions
    # genuinely ARE fingerprinted, so this is coherent, not
    # nonsensical), fix the stale docstring instead. This is the
    # positive-match test that decision needed -- the sweep's own
    # test only proved "does not raise," never a real match.
    def test_finds_the_matching_version_with_real_path_and_uuid(self):
        results = _finder(
            '$acme.csvpaths.:fingerprint("cccc")', manifest=FINGERPRINT_MANIFEST
        ).query()
        assert results.files == [GROUP_FILE_PATH]
        assert results.uuids == ["v1-uuid"]

    def test_no_match_gives_empty(self):
        results = _finder(
            '$acme.csvpaths.:fingerprint("nope")', manifest=FINGERPRINT_MANIFEST
        ).query()
        assert results.results == []

    def test_combines_with_name_three(self):
        # not-yet-supported sweep #9, 2026-10-20 -- same fix as
        # TestBareUuidLookup's own test above, shared code. "0" is
        # v1-uuid's own real identity (FINGERPRINT_MANIFEST above).
        results = _finder(
            '$acme.csvpaths.:fingerprint("cccc").0',
            manifest=FINGERPRINT_MANIFEST,
        ).query()
        assert results.uuids == ["v1-uuid"]
        assert results.results[0].identity == "0"

    def test_combined_with_name_three_no_match_gives_empty(self):
        results = _finder(
            '$acme.csvpaths.:fingerprint("cccc").company_names',
            manifest=FINGERPRINT_MANIFEST,
        ).query()
        assert results.results == []

    # beside a pointer it filters, the same as ':uuid()' (2026-11-06)
    @pytest.mark.parametrize(
        "reference, expected",
        [
            ('$acme.csvpaths.:last():fingerprint("aaaa")', ["v0-uuid"]),
            ('$acme.csvpaths.:fingerprint("aaaa"):last()', ["v0-uuid"]),
            ('$acme.csvpaths.:all():fingerprint("cccc")', ["v1-uuid"]),
            ('$acme.csvpaths.:last():fingerprint("x")', []),
        ],
    )
    def test_an_argument_beside_a_pointer_filters(self, reference, expected):
        results = _finder(reference, manifest=FINGERPRINT_MANIFEST).query()
        assert results.uuids == expected


class TestNoPointerReturnsEveryVersion:
    # a chain with no pointer at all (e.g. a bare :all()) does not
    # narrow to one version -- every version in the manifest comes
    # back, unreduced. This is how "Name_one used alone == list of
    # versions in the form: (path-to-group.csvpaths, uuid)" (STRUCTURE
    # table) is actually reached.
    def test_bare_all_returns_every_version(self):
        results = _finder("$acme.csvpaths.:all()").query()
        assert results.files == [GROUP_FILE_PATH, GROUP_FILE_PATH]
        assert results.uuids == ["v0-uuid", "v1-uuid"]

    def test_all_combined_with_name_three_filters_each_version(self):
        # only versions containing the matching identity come back --
        # "company_names" only exists in v0's identities.
        results = _finder("$acme.csvpaths.:all().company_names").query()
        assert results.uuids == ["v0-uuid"]

    def test_all_with_no_matches_at_all_returns_empty(self):
        results = _finder("$acme.csvpaths.:all().nope").query()
        assert results.files == []


class TestHaving:
    # ':having("identity")' -- added 2026-08-13, filters the version
    # list down to versions whose own "named_paths_identities" actually
    # contains that identity, before any pointer reduces further --
    # "company_names" only exists in ACME_MANIFEST's v0.
    def test_having_then_pointer_reduces_the_filtered_list(self):
        results = _finder("$acme.csvpaths.:having(\"company_names\"):last()").query()
        assert results.uuids == ["v0-uuid"]

    def test_having_alone_lists_matching_versions_unreduced(self):
        results = _finder('$acme.csvpaths.:having("company_names")').query()
        assert results.uuids == ["v0-uuid"]

    def test_having_with_no_matching_version_is_empty(self):
        results = _finder('$acme.csvpaths.:having("nope")').query()
        assert results.uuids == []

    def test_having_matches_an_unnamed_statements_stringified_index_too(self):
        # v1's sole statement is unnamed -- its identity is "0" (the
        # stringified load-time index), same convention name_three
        # identity lookups already use.
        results = _finder('$acme.csvpaths.:having("0"):last()').query()
        assert results.uuids == ["v1-uuid"]

    def test_having_requires_an_argument(self):
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:having():last()").query()

    def test_having_rejects_a_nested_function_argument(self):
        # ':having()'s own ARG_TYPES widened 2026-10-18 to also accept
        # a nested function (RESULTS' own need, see test_results_
        # reference_finder_3.py's TestHavingNestedFieldAccessor) --
        # CSVPATHS has no per-statement field to match against (no
        # per-statement uuid at all), so it still only accepts a plain
        # identity string, now explicitly rejected rather than
        # silently matching nothing.
        with pytest.raises(ReferenceException3):
            _finder('$acme.csvpaths.:having(:uuid("x")):last()').query()

    def test_having_accepts_a_list_for_any_of_these_identities(self):
        # widened again 2026-10-18 (same day) -- a list is only ever
        # reachable via an `@variable` (the grammar has no literal list
        # syntax); confirmed live before this that a list-valued
        # variable raised ReferenceRuntimeException3 outright. v0 has
        # "company_names"; neither version has "nope".
        results = _finder(
            "$acme.csvpaths.:having(@identities):last()",
            variables={"identities": ["company_names", "nope"]},
        ).query()
        assert results.uuids == ["v0-uuid"]

    def test_having_list_with_no_match_at_all_is_empty(self):
        results = _finder(
            "$acme.csvpaths.:having(@identities):last()",
            variables={"identities": ["nope", "also-nope"]},
        ).query()
        assert results.uuids == []


VERSION_RANGE_GROUP_FILE_PATH = "named_paths/dater/group.csvpath"
VERSION_RANGE_MANIFEST = [
    {
        "group_file_path": VERSION_RANGE_GROUP_FILE_PATH,
        "uuid": f"v{i}-uuid",
        "named_paths": [f"stmt {i} text"],
        "named_paths_identities": [str(i)],
        "time": f"2026-01-0{i + 1}T00:00:00+00:00",
    }
    for i in range(5)
]


class TestVersionRange:
    # ':from()'/':to()' as a name_one VERSION range -- added 2026-08-13,
    # David: a named-paths group's own load time is a real arrival-date
    # concept ("give me the versions loaded between date-one and
    # date-two"), the same one RESULTS'/FILES' own version-level ranges
    # already filter by. Windows the (possibly ':having()'-filtered)
    # manifest -- a real pointer riding alongside reduces the RANGE, not
    # the full candidate set, same as RESULTS/FILES.
    def test_from_index_negative_gives_the_last_n_versions(self):
        results = _finder(
            "$dater.csvpaths.:from(-2)", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v3-uuid", "v4-uuid"]

    def test_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            "$dater.csvpaths.:from(1):to(3)", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v1-uuid", "v2-uuid", "v3-uuid"]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # the normative example, verbatim: ":date("2026-01-31")"
            # expands to the very first moment of the 31st, so this
            # reference effectively misses one day (6.27b, 6.27g;
            # decision D8, 2026-11-12). It kept the whole 31st until then.
            (
                '$dater.csvpaths.:from(:date("2026-01-01"))'
                ':to(:date("2026-01-31"))',
                ["jan-1", "jan-15", "jan-15-noon", "jan-31-midnight"],
            ),
            # ':after()' a day keeps the rest of that day; the day's last
            # moment is needed to mean after it (the normative note)
            (
                '$dater.csvpaths.:after(:date("2026-01-15"))',
                ["jan-15-noon", "jan-31-midnight", "jan-31-noon"],
            ),
            (
                '$dater.csvpaths.:after(:date("2026-01-15_23-59-59"))',
                ["jan-31-midnight", "jan-31-noon"],
            ),
            (
                '$dater.csvpaths.:before(:date("2026-01-31"))',
                ["jan-1", "jan-15", "jan-15-noon"],
            ),
        ],
    )
    def test_a_date_anchor_is_its_first_moment(self, reference, expected):
        manifest = [
            {"group_file_path": GROUP_FILE_PATH, "uuid": uuid, "time": time}
            for uuid, time in (
                ("jan-1", "2026-01-01T00:00:00+00:00"),
                ("jan-15", "2026-01-15T00:00:00+00:00"),
                ("jan-15-noon", "2026-01-15T12:00:00+00:00"),
                ("jan-31-midnight", "2026-01-31T00:00:00+00:00"),
                ("jan-31-noon", "2026-01-31T12:00:00+00:00"),
            )
        ]
        assert _finder(reference, manifest).query().uuids == expected

    def test_a_pointer_reduces_the_range_not_the_full_candidate_set(self):
        results = _finder(
            "$dater.csvpaths.:from(-3):last()", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v4-uuid"]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # directionals set the range before an anchor does (NRE;
            # David, spec review item 4): ':last()' is the range's last
            ("$dater.csvpaths.:from(-4):to(-2):last()", ["v3-uuid"]),
            ("$dater.csvpaths.:from(-4):to(-2):first()", ["v1-uuid"]),
        ],
    )
    def test_a_pointer_selects_within_a_two_directional_range(
        self, reference, expected
    ):
        assert _finder(reference, VERSION_RANGE_MANIFEST).query().uuids == expected

    def test_a_pointer_selects_within_each_groups_range_under_star(self):
        # '*' groups (4.1b): each group's own range, then its own pick
        results = _star_finder("$*.csvpaths.:from(-2):to(-1):first()").query()
        assert sorted(results.uuids) == ["a-v1", "b-v1"]

    def test_date_mode_from_filters_by_the_versions_own_load_time(self):
        results = _finder(
            '$dater.csvpaths.:from(:date("2026-01-03"))', VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2-uuid", "v3-uuid", "v4-uuid"]

    def test_date_mode_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            '$dater.csvpaths.:from("2026-01-02"):to("2026-01-04")',
            VERSION_RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v1-uuid", "v2-uuid", "v3-uuid"]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # index and date bounds may mix (6.32, NRE 781): the index
            # bound is a position in the whole list, the date bound a
            # filter, and the range is both. These raised until 2026-11-12.
            ('$dater.csvpaths.:from(1):to(:date("2026-01-01"))', []),
            (
                '$dater.csvpaths.:from(1):to(:date("2026-01-03"))',
                ["v1-uuid", "v2-uuid"],
            ),
            (
                '$dater.csvpaths.:after(1):before(:date("2026-01-05"))',
                ["v2-uuid", "v3-uuid"],
            ),
        ],
    )
    def test_index_and_date_bounds_mix(self, reference, expected):
        assert _finder(reference, VERSION_RANGE_MANIFEST).query().uuids == expected

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # David, 2026-11-14 (decision W4): an index counts from the date
            # anchor (6.30). The date bound filters first, then the index
            # counts within what is left. Counted from the start, these
            # would give v1-v3 and v2-v3. They raised "not settled".
            (
                '$dater.csvpaths.:from(:date("2026-01-02")):to(3)',
                ["v1-uuid", "v2-uuid", "v3-uuid", "v4-uuid"],
            ),
            (
                '$dater.csvpaths.:from(-3):to(:date("2026-01-04"))',
                ["v1-uuid", "v2-uuid", "v3-uuid"],
            ),
        ],
    )
    def test_an_index_counts_from_the_date_anchor(self, reference, expected):
        assert _finder(reference, VERSION_RANGE_MANIFEST).query().uuids == expected

    def test_date_mode_accepts_the_optional_time_suffix(self):
        # issue #409 -- David's own exact repro:
        # "$acme.csvpaths.:before(:date(\"2026-10-20_17-00-00\"))" used
        # to raise outright. Every fixture entry's own "time" is
        # exactly midnight, so a time-suffixed bound at midnight gives
        # the identical result to the plain date-only bound just above.
        results = _finder(
            '$dater.csvpaths.:from(:date("2026-01-03_00-00-00"))',
            VERSION_RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v2-uuid", "v3-uuid", "v4-uuid"]

    def test_date_mode_time_suffix_narrows_to_the_named_second(self):
        # v2-uuid's own time is exactly "2026-01-03T00:00:00" -- a
        # bound one hour later on the same day excludes it, proving
        # the time suffix is real second-granularity, not silently
        # ignored/truncated back to day-granularity.
        results = _finder(
            '$dater.csvpaths.:from(:date("2026-01-03_01-00-00"))',
            VERSION_RANGE_MANIFEST,
        ).query()
        assert results.uuids == ["v3-uuid", "v4-uuid"]

    def test_a_malformed_date_bound_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$dater.csvpaths.:from("not-a-date")', VERSION_RANGE_MANIFEST
            ).query()

    def test_a_name_bound_on_versions_raises(self):
        # versions have no statement identity; a string here is a date, so
        # a ':name()' bound must not be read as one (2026-11-13)
        with pytest.raises(ReferenceException3, match="statement identit"):
            _finder(
                '$dater.csvpaths.:from(:name("2026-01-01"))', VERSION_RANGE_MANIFEST
            ).query()

    def test_bare_time_window_function_is_a_range_matching_6_27e(self):
        # Gap 1 of compendium 6.27/TimeWindowFunction3, added 2026-10-17
        # -- a BARE time-component function riding in the chain, no
        # explicit :from()/:to() -- 6.27e's first bullet, "use as a
        # range." Pinned to 2026-01-04 (v3's own load time).
        from datetime import date

        from csvpath.util.date_util import DateUtility as daut

        real_now = daut.now()
        daut.OFFSET_DAYS = (date(2026, 1, 4) - real_now.date()).days
        try:
            results = _finder(
                "$dater.csvpaths.:yesterday()", VERSION_RANGE_MANIFEST
            ).query()
            assert results.uuids == ["v2-uuid"]
        finally:
            daut.OFFSET_DAYS = 0

    def test_bare_time_window_combined_with_explicit_range_is_rejected(
        self,
    ):
        with pytest.raises(ReferenceException3):
            _finder(
                "$dater.csvpaths.:yesterday():from(1)", VERSION_RANGE_MANIFEST
            ).query()

    def test_time_window_function_nested_anchor_also_works_for_csvpaths(
        self,
    ):
        # Gap 2 of compendium 6.27/TimeWindowFunction3 (added 2026-10-17)
        # -- confirmed live for CSVPATHS too, not just assumed from the
        # shared mechanism. Pins "now" to 2026-01-04 (v3's own load
        # time) via DateUtility.OFFSET_DAYS.
        from datetime import date

        from csvpath.util.date_util import DateUtility as daut

        real_now = daut.now()
        daut.OFFSET_DAYS = (date(2026, 1, 4) - real_now.date()).days
        try:
            results = _finder(
                "$dater.csvpaths.:from(:year())", VERSION_RANGE_MANIFEST
            ).query()
            assert results.uuids == [
                "v0-uuid",
                "v1-uuid",
                "v2-uuid",
                "v3-uuid",
                "v4-uuid",
            ]
            results = _finder(
                "$dater.csvpaths.:before(:today())", VERSION_RANGE_MANIFEST
            ).query()
            assert results.uuids == ["v0-uuid", "v1-uuid", "v2-uuid"]
        finally:
            daut.OFFSET_DAYS = 0

    def test_having_filters_before_the_range_windows(self):
        # ':having("4")' only matches v4, so the range (last 3) has just
        # that one entry to window -- confirms the two compose in the
        # order the docstring describes (having, then range, then
        # pointer), not independently.
        results = _finder(
            '$dater.csvpaths.:having("4"):from(-3)', VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v4-uuid"]

    def test_range_combined_with_star_traversal(self):
        # changed 2026-11-06: '*' used to reject a range. Within the one
        # group, the last of the last two versions is v4.
        results = _finder(
            "$*.csvpaths.:from(-2):last()",
            VERSION_RANGE_MANIFEST,
            by_name={"dater": VERSION_RANGE_MANIFEST},
        ).query()
        assert results.uuids == [VERSION_RANGE_MANIFEST[-1]["uuid"]]


class TestVersionDirectionFunctions:
    # ':before()'/':after()' as a name_one VERSION range -- compendium
    # 6.28/6.28b/6.28c, built 2026-10-16, the EXCLUSIVE siblings of
    # ':to()'/':from()'. VERSION_RANGE_MANIFEST is v0..v4, positions
    # 0-4, dates 2026-01-01..2026-01-05.
    def test_after_excludes_its_own_position(self):
        results = _finder("$dater.csvpaths.:after(1)", VERSION_RANGE_MANIFEST).query()
        assert results.uuids == ["v2-uuid", "v3-uuid", "v4-uuid"]

    def test_before_excludes_its_own_position(self):
        results = _finder("$dater.csvpaths.:before(3)", VERSION_RANGE_MANIFEST).query()
        assert results.uuids == ["v0-uuid", "v1-uuid", "v2-uuid"]

    def test_after_and_before_together_is_an_exclusive_range(self):
        results = _finder(
            "$dater.csvpaths.:after(1):before(4)", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2-uuid", "v3-uuid"]

    def test_date_mode_after_excludes_its_own_date(self):
        results = _finder(
            '$dater.csvpaths.:after("2026-01-02")', VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2-uuid", "v3-uuid", "v4-uuid"]

    def test_date_mode_before_excludes_its_own_date(self):
        results = _finder(
            '$dater.csvpaths.:before("2026-01-04")', VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v0-uuid", "v1-uuid", "v2-uuid"]

    def test_combining_two_lower_bounds_is_illegal(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$dater.csvpaths.:from(1):after(2)", VERSION_RANGE_MANIFEST
            ).query()

    def test_combining_two_upper_bounds_is_illegal(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$dater.csvpaths.:to(3):before(1)", VERSION_RANGE_MANIFEST
            ).query()

    def test_below_and_above_aliases_work(self):
        results = _finder(
            "$dater.csvpaths.:above(1):below(4)", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v2-uuid", "v3-uuid"]


class TestIdentityLookupOnNameThree:
    def test_matches_named_identity(self):
        results = _finder("$acme.csvpaths.:first().company_names").query()
        assert results.uuids == ["v0-uuid"]

    def test_matches_stringified_index_identity(self):
        results = _finder("$acme.csvpaths.:last().0").query()
        assert results.uuids == ["v1-uuid"]

    def test_no_matching_identity_returns_empty(self):
        results = _finder("$acme.csvpaths.:first().nope").query()
        assert results.files == []

    def test_name_three_does_not_change_path_or_uuid(self):
        # per the STRUCTURE table: querying at name_three gives the same
        # (path, uuid) as name_one alone for csvpaths -- name_three only
        # adds an existence constraint, it does not select a different
        # physical thing (there isn't one -- one file, one uuid per
        # version, regardless of which statement within it). identity
        # DOES differ (added 2026-08-13, see ReferenceResult3.identity's
        # own docstring) -- that is the whole point of it, not a bug.
        with_three = _finder("$acme.csvpaths.:first().company_names").query()
        without_three = _finder("$acme.csvpaths.:first()").query()
        assert with_three.files == without_three.files
        assert with_three.uuids == without_three.uuids
        assert with_three.results[0].identity == "company_names"
        assert without_three.results[0].identity is None


RANGE_GROUP_FILE_PATH = "named_paths/ranger/group.csvpath"
RANGE_MANIFEST = [
    {
        "group_file_path": RANGE_GROUP_FILE_PATH,
        "uuid": "range-uuid",
        "named_paths": [
            "stmt one text",
            "stmt two text",
            "stmt three text",
            "stmt four text",
            "stmt five text",
        ],
        "named_paths_identities": ["one", "two", "three", "four", "five"],
    },
]


class TestNameThreeRange:
    # ':from()'/':to()' as a name_three statement range -- added
    # 2026-08-13, David's own FlightPath v2 use case: rewind/replay
    # starting from a specific csvpath statement (e.g.
    # "$acme.csvpaths.:last().:from(:index(2))"). Windows the matched
    # version's own ordered "named_paths_identities" list; each windowed
    # result carries its OWN identity since csvpaths has no per-
    # statement uuid (see ReferenceResult3.identity's own docstring).
    def test_from_index_negative_gives_the_last_n(self):
        results = _finder(
            "$ranger.csvpaths.:first().:from(-2)", RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["four", "five"]
        assert results.uuids == ["range-uuid", "range-uuid"]
        assert results.files == [RANGE_GROUP_FILE_PATH, RANGE_GROUP_FILE_PATH]

    def test_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            "$ranger.csvpaths.:first().:from(:index(1)):to(:index(3))",
            RANGE_MANIFEST,
        ).query()
        assert [r.identity for r in results.results] == ["two", "three", "four"]

    def test_resolve_gives_each_windowed_statements_own_text(self):
        results = _finder(
            "$ranger.csvpaths.:first().:from(:index(1)):to(:index(2))",
            RANGE_MANIFEST,
        ).resolve()
        assert [r.data for r in results.results] == [
            "stmt two text",
            "stmt three text",
        ]

    def test_date_mode_is_not_supported(self):
        # csvpaths statements have no arrival date of their own -- only
        # index-mode bounds are meaningful.
        with pytest.raises(ReferenceException3):
            _finder(
                '$ranger.csvpaths.:first().:from(:date("2025-01-01"))',
                RANGE_MANIFEST,
            ).query()

    def test_time_window_function_bound_is_also_not_supported(self):
        # widened 2026-10-17 (compendium 6.27, TimeWindowFunction3) from
        # Date3-only -- every sibling time-component function is
        # rejected here for the same reason.
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.csvpaths.:first().:from(:year())", RANGE_MANIFEST
            ).query()

    def test_combining_a_literal_identity_with_a_range_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.csvpaths.:first().one:from(-1)", RANGE_MANIFEST
            ).query()

    def test_an_unrecognized_function_on_name_three_is_rejected(self):
        # anything other than a literal identity or ':from()'/':to()'
        # is not yet supported on name_three -- e.g. a pointer riding
        # alongside the range, which FILES allows but csvpaths does not.
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.csvpaths.:first().:from(-2):last()", RANGE_MANIFEST
            ).query()

    def test_identity_mode_selects_the_inclusive_range_between_two_names(self):
        # added 2026-09-22, per normative_reference_examples.txt's own
        # "Select sequential statements" worked example -- a bare string
        # bound resolves to ITS OWN position via _find_by_identity()
        # first, then the range slices positionally, same as index-mode.
        results = _finder(
            '$ranger.csvpaths.:first().:from("two"):to("four")', RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["two", "three", "four"]

    def test_a_name_bound_is_a_statement_identity(self):
        # NRE "Identities": "`:name()` with a string ... equaling the
        # statement identity", the same as a bare string (2026-11-13)
        results = _finder(
            '$ranger.csvpaths.:first().:from(:name("two")):to(:name("four"))',
            RANGE_MANIFEST,
        ).query()
        assert [r.identity for r in results.results] == ["two", "three", "four"]

    def test_a_name_bound_takes_a_variable(self):
        finder = _finder(
            '$ranger.csvpaths.:first().:from(:name(@x)):to(:name("four"))',
            RANGE_MANIFEST,
        )
        finder.set_variable("x", value="two")
        assert [r.identity for r in finder.query().results] == [
            "two",
            "three",
            "four",
        ]

    # decision D12 (spec pass, 2026-11-14): an int ':name()' is the
    # statement identity of that string. NRE "Identities": "the index is
    # also used as the name, if another name is not assigned". Statement 2
    # here is named "header", so its identity is not "2".
    UNNAMED_MANIFEST = [
        dict(
            RANGE_MANIFEST[0],
            named_paths_identities=["0", "1", "header", "3", "4"],
        )
    ]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$ranger.csvpaths.:first().:from(:name(1)):to(:name(3))", ["1", "header", "3"]),
            ("$ranger.csvpaths.:first().:from(:name(3))", ["3", "4"]),
            # no statement has the identity "2": nothing, no error (NRE)
            ("$ranger.csvpaths.:first().:from(:name(2))", []),
            # the index is always there, named or not
            ("$ranger.csvpaths.:first().:from(2)", ["header", "3", "4"]),
        ],
    )
    def test_an_int_name_bound_is_the_identity_of_that_string(
        self, reference, expected
    ):
        results = _finder(reference, self.UNNAMED_MANIFEST).query()
        assert [r.identity for r in results.results] == expected

    def test_an_int_name_bound_takes_a_variable(self):
        finder = _finder(
            "$ranger.csvpaths.:first().:from(:name(@x))", self.UNNAMED_MANIFEST
        )
        finder.set_variable("x", value=3)
        assert [r.identity for r in finder.query().results] == ["3", "4"]

    def test_a_name_bound_that_does_not_match_gives_nothing(self):
        results = _finder(
            '$ranger.csvpaths.:first().:from(:name("nope"))', RANGE_MANIFEST
        ).query()
        assert results.results == []

    def test_identity_mode_resolve_gives_each_windowed_statements_own_text(self):
        results = _finder(
            '$ranger.csvpaths.:first().:from("one"):to("two")', RANGE_MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == [
            "stmt one text",
            "stmt two text",
        ]

    def test_identity_mode_one_sided_from_gives_an_open_ended_range(self):
        results = _finder(
            '$ranger.csvpaths.:first().:from("four")', RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["four", "five"]

    def test_identity_mode_no_match_gives_no_results_not_an_error(self):
        # per the normative doc: "if the names given do not match, the
        # reference returns no results, no error is thrown, and no
        # partial results given."
        results = _finder(
            '$ranger.csvpaths.:first().:from("nonexistent"):to("four")',
            RANGE_MANIFEST,
        ).query()
        assert results.results == []

    def test_identity_mode_can_mix_with_an_index_mode_bound(self):
        # not ambiguous the way name_one's index/date mixing is -- both
        # identity and index bounds resolve to plain int positions
        # before slicing, so a mixed pair like this has one clear
        # meaning: "two" through position 3 (four).
        results = _finder(
            '$ranger.csvpaths.:first().:from("two"):to(3)', RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["two", "three", "four"]

    def test_after_excludes_its_own_index_position(self):
        # identities: ["one","two","three","four","five"], positions 0-4.
        results = _finder(
            "$ranger.csvpaths.:first().:after(1)", RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["three", "four", "five"]

    def test_before_excludes_its_own_index_position(self):
        results = _finder(
            "$ranger.csvpaths.:first().:before(3)", RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["one", "two", "three"]

    def test_after_excludes_its_own_named_identity(self):
        # the exclusive adjustment applies AFTER identity-to-position
        # resolution -- "after 'two'" (position 1) means position 2
        # onward, i.e. "three" is INCLUDED, not excluded.
        results = _finder(
            '$ranger.csvpaths.:first().:after("two")', RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["three", "four", "five"]

    def test_before_excludes_its_own_named_identity(self):
        results = _finder(
            '$ranger.csvpaths.:first().:before("four")', RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["one", "two", "three"]

    def test_after_and_before_together_is_an_exclusive_range(self):
        results = _finder(
            "$ranger.csvpaths.:first().:after(0):before(4)", RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["two", "three", "four"]

    def test_combining_two_upper_bounds_is_illegal(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$ranger.csvpaths.:first().:to(3):before(1)", RANGE_MANIFEST
            ).query()


class TestResolve:
    def test_resolving_a_named_identity_gives_its_statement_text(self):
        results = _finder("$acme.csvpaths.:first().company_names").resolve()
        assert results.results[0].data == "stmt text A"

    def test_resolving_a_stringified_index_identity_gives_its_statement_text(self):
        results = _finder("$acme.csvpaths.:last().0").resolve()
        assert results.results[0].data == "stmt text C"

    def test_resolving_with_no_name_three_gives_none(self):
        # a whole group version has no single unambiguous payload.
        results = _finder("$acme.csvpaths.:last()").resolve()
        assert results.results[0].data is None

    @pytest.mark.parametrize(
        "statements",
        [
            # no named_paths at all, and one shorter than the identities
            None,
            ["stmt text A"],
        ],
    )
    @pytest.mark.parametrize(
        "reference", ["$acme.csvpaths.:first().1", "$*.csvpaths.:first().1"]
    )
    def test_a_statement_list_shorter_than_its_identities_raises(
        self, reference, statements
    ):
        # named_paths_identities and named_paths are parallel lists. When
        # they disagree, resolve raised a bare IndexError (2026-11-12).
        entry = {k: v for k, v in ACME_MANIFEST[0].items() if k != "named_paths"}
        if statements is not None:
            entry["named_paths"] = statements
        finder = _finder(
            reference,
            by_name={"acme": [entry]},
            inputs_csvpaths_path="inputs/named_paths",
        )
        with pytest.raises(ReferenceException3) as error:
            finder.resolve()
        message = str(error.value)
        assert "v0-uuid" in message
        assert "'1'" in message
        assert "disagree" in message
        if statements is None:
            assert "has no named_paths" in message
        else:
            assert "has only 1 statement(s)" in message


class TestManifestFunction:
    # ":manifest()" is a name_one-terminal, bare/sole-content shape --
    # it bypasses _resolve_versions()'s version-selection pipeline
    # entirely and points at the named-paths group's own manifest.json
    # instead (one fixed resource per group, covering every version).
    def test_query_returns_the_manifest_path_with_no_uuid(self):
        results = _finder("$acme.csvpaths.:manifest()").query()
        assert results.files == [pathu.resep(f"{GROUP_HOME}/manifest.json")]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_manifest_files_raw_bytes(self, tmp_path):
        content = b"[]"
        home = tmp_path / "acme"
        home.mkdir()
        (home / "manifest.json").write_bytes(content)
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(string="$acme.csvpaths.:manifest()", csvpaths=csvpaths)
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_manifest_beside_a_version_pointer_gives_the_one_matched_entry(self):
        # :manifest() never narrows/selects itself (VALUE role, not
        # POINTER -- see functions/manifest_3.py) -- it can ride
        # alongside :last() in the same combined chain without tripping
        # "at most one pointer per chain". :last() still reduces to one
        # version; :manifest() changes what that version resolves to.
        results = _finder("$acme.csvpaths.:last():manifest()").resolve()
        assert results.uuids == ["v1-uuid"]
        assert results.results[0].data == ACME_MANIFEST[1]

    def test_manifest_with_all_and_no_pointer_raises(self):
        # :all() (CONTEXT_SETTER) plus :manifest() (VALUE) -- neither is
        # a pointer, and ACME_MANIFEST has two versions. Resolving full
        # manifest content always touches exactly one entity (settled
        # 2026-08-07), so this is illegal -- a pointer is required to
        # pick one version. query() itself succeeds (moved 2026-08-26,
        # see the ":path()" retirement/Rule 1 bucket-list entry) -- only
        # resolve() raises, once something actually tries to read the
        # content.
        finder = _finder("$acme.csvpaths.:all():manifest()")
        assert len(finder.query()) > 1
        with pytest.raises(ReferenceException3):
            finder.resolve()

    def test_manifest_with_no_pointer_and_exactly_one_version_still_works(self):
        single_version = [ACME_MANIFEST[0]]
        results = _finder("$acme.csvpaths.:all():manifest()", single_version).resolve()
        assert results.uuids == ["v0-uuid"]
        assert results.results[0].data == single_version[0]


class TestManifestFieldOverSeveralVersions:
    # Rule 3 (manifest_field_functions_proposal.md): a field is a small
    # value, so it can be read for several versions at once; Rule 1 still
    # stops whole entries. Before 2026-11-08 a field beside a multi-version
    # ':manifest()' raised on resolve, where FILES gives one value per
    # version.
    @pytest.mark.parametrize(
        "reference, expected",
        [
            (
                "$dater.csvpaths.:manifest():from(1):to(2):uuid()",
                ["v1-uuid", "v2-uuid"],
            ),
            (
                "$dater.csvpaths.:from(1):to(2):manifest():uuid()",
                ["v1-uuid", "v2-uuid"],
            ),
            (
                "$dater.csvpaths.:all():manifest():uuid()",
                ["v0-uuid", "v1-uuid", "v2-uuid", "v3-uuid", "v4-uuid"],
            ),
            (
                "$dater.csvpaths.:manifest():from(-2):named_paths_identities()",
                [["3"], ["4"]],
            ),
            (
                "$dater.csvpaths.:manifest():from(1):to(2):time()",
                ["2026-01-02T00:00:00+00:00", "2026-01-03T00:00:00+00:00"],
            ),
        ],
    )
    def test_a_field_resolves_one_value_per_version(self, reference, expected):
        finder = _finder(reference, VERSION_RANGE_MANIFEST)
        assert not finder.query().ambiguous_content_read
        assert [r.data for r in finder.resolve().results] == expected

    def test_a_keyed_definition_field_is_not_read_per_version(self):
        # a "{}"-key field's argument picks the key; it is not a gate.
        # It reads definition.json, which has no versions, so a range
        # beside it raises (David, 2026-11-10). Gave the same address
        # three times.
        reference = (
            '$acme.csvpaths.:manifest():from(0):to(2):destination_address("myd")'
        )
        with pytest.raises(ReferenceException3) as error:
            _gate_finder(reference).query()
        assert "definition.json, which is not versioned" in str(error.value)
        results = _gate_finder('$acme.csvpaths.:destination_address("myd")').resolve()
        assert [r.data for r in results.results] == ["ftp.acme.example"]

    @pytest.mark.parametrize(
        "reference",
        [
            "$dater.csvpaths.:manifest():from(1):to(2)",
            "$dater.csvpaths.:from(1):to(2):manifest()",
            "$dater.csvpaths.:all():manifest()",
        ],
    )
    def test_whole_entries_for_several_versions_still_raise(self, reference):
        finder = _finder(reference, VERSION_RANGE_MANIFEST)
        results = finder.query()
        assert len(results) > 1
        assert results.ambiguous_content_read
        with pytest.raises(ReferenceException3) as error:
            finder.resolve()
        assert "more than one match" in str(error.value)

    def test_a_pointer_after_the_range_still_gives_the_whole_entry(self):
        finder = _finder(
            "$dater.csvpaths.:manifest():from(1):to(2):last()",
            VERSION_RANGE_MANIFEST,
        )
        assert [r.data for r in finder.resolve().results] == [
            VERSION_RANGE_MANIFEST[2]
        ]


class TestGlobalLoadsLedger:
    # Rule 1a: "*" at root_major combined with a bare :manifest() is the
    # one exception to root_major=="*" being unsupported -- it resolves
    # to the Named-Paths Loads Manifest, a single global ledger at the
    # named-paths root tracking every load across every named-paths
    # group.
    def test_query_returns_the_global_ledger_path_with_no_uuid(self):
        results = _finder(
            "$*.csvpaths.:manifest()",
            inputs_csvpaths_path="inputs/named_paths",
        ).query()
        assert results.files == [pathu.resep("inputs/named_paths/manifest.json")]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_global_ledgers_raw_bytes(self, tmp_path):
        content = b'[{"named_paths_name": "acme"}, {"named_paths_name": "beta"}]'
        root = tmp_path / "named_paths"
        root.mkdir()
        (root / "manifest.json").write_bytes(content)
        finder = _finder(
            "$*.csvpaths.:manifest()", inputs_csvpaths_path=str(root)
        )
        results = finder.resolve()
        assert results.results[0].data == content

    def test_star_with_definition_is_one_file_per_group(self):
        # raised until 2026-11-10; now each live group's definition.json,
        # as FILES gives each named-file's. Several whole files cannot be
        # resolved at once (Rule 1), so the result is flagged.
        finder = _gate_finder("$*.csvpaths.:definition()")
        results = finder.query()
        assert results.files == [
            pathu.resep("named_paths/acme/definition.json"),
            pathu.resep("named_paths/beta/definition.json"),
        ]
        assert results.uuids == [None, None]
        assert results.ambiguous_content_read
        with pytest.raises(ReferenceException3):
            finder.resolve()

    def test_star_root_major_with_no_named_paths_groups_gives_empty_results(self):
        # '*' traversal is supported now (see TestStarTraversal below) --
        # with zero named-paths groups to enumerate (no by_name given
        # here), it correctly finds nothing rather than raising.
        finder = _finder(
            "$*.csvpaths.:last()", inputs_csvpaths_path="inputs/named_paths"
        )
        assert finder.query().results == []


LOADS_LEDGER = [
    {"named_paths_name": "acme", "uuid": "u-loads-1"},
    {"named_paths_name": "beta", "uuid": "u-loads-2"},
    {"named_paths_name": "gamma", "uuid": "u-loads-3"},
]


class TestGlobalLoadsLedgerOrdinalIndexing:
    # Rule 1b: a pointer (:first()/:last()/:index(n)) riding before the
    # bare :manifest() selects one entry out of the ledger by ordinal
    # position, instead of dumping the whole thing.
    def test_last_gives_the_most_recent_load(self):
        finder = _finder(
            "$*.csvpaths.:last():manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LOADS_LEDGER[-1]

    def test_index_gives_the_nth_load(self):
        finder = _finder(
            "$*.csvpaths.:index(0):manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.resolve()
        assert results.results[0].data == LOADS_LEDGER[0]

    def test_out_of_range_index_gives_no_results(self):
        finder = _finder(
            "$*.csvpaths.:index(99):manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.query()
        assert len(results.results) == 0

    def test_query_gives_the_ledger_path_with_the_entrys_own_uuid(self):
        finder = _finder(
            "$*.csvpaths.:last():manifest()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.query()
        assert results.files == [pathu.resep("inputs/named_paths/manifest.json")]
        assert results.results[0].uuid == "u-loads-3"

    def test_manifest_then_pointer_order_also_works(self):
        # order-insensitivity was missing on _pointer_before_manifest
        # and fixed 2026-08-10.
        finder = _finder(
            "$*.csvpaths.:manifest():last()",
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        )
        results = finder.query()
        assert results.results[0].uuid == "u-loads-3"


#
# named-paths group alpha (2 versions) + beta (1 version). beta is
# listed FIRST in STAR_BY_NAME on purpose -- naive concatenation with no
# time-sort would put alpha's own last entry last in the pooled list, so
# a test asserting beta's true-latest entry wins would fail if the
# flatten case's time-sort were ever removed/broken.
#
STAR_ALPHA_MANIFEST = [
    {
        "group_file_path": "named_paths/alpha/group.csvpath",
        "uuid": "a-v1",
        "time": "2026-01-01T00:00:00+00:00",
    },
    {
        "group_file_path": "named_paths/alpha/group.csvpath",
        "uuid": "a-v2",
        "time": "2026-01-02T00:00:00+00:00",
    },
]
STAR_BETA_MANIFEST = [
    {
        "group_file_path": "named_paths/beta/group.csvpath",
        "uuid": "b-v1",
        "time": "2026-01-03T00:00:00+00:00",
        "named_paths_identities": ["orders", "1"],
    },
]
STAR_BY_NAME = {"beta": STAR_BETA_MANIFEST, "alpha": STAR_ALPHA_MANIFEST}


def _star_finder(reference: str) -> CsvpathsReferenceFinder3:
    # inputs_csvpaths_path is needed even for genuine (non-Rule-1a/1b)
    # traversal now: _extract_data()'s Star3 branch always computes the
    # ledger's own fixed path to disambiguate against, whether or not
    # this particular reference turns out to be the ledger-ordinal case
    # (fixed 2026-08-26, see csvpaths_reference_finder_3.py).
    return _finder(
        reference, by_name=STAR_BY_NAME, inputs_csvpaths_path="inputs/named_paths"
    )


class TestStarTraversalFlatten:
    # bare pointer, no ':all()' -- '*' mimics grouping (compendium 4.1b,
    # finding I, David 2026-10-30/2026-11-03): the pointer applies within
    # each named-paths group, one result per group. Was pooled, one
    # result in total: "$*.csvpaths.:last()" gave b-v1 alone.
    def test_last_is_each_groups_last_version(self):
        # alpha's own last version (a-v2) comes back beside beta's, though
        # beta's is the most recent overall
        results = _star_finder("$*.csvpaths.:last()").query()
        assert sorted(results.uuids) == ["a-v2", "b-v1"]

    def test_first_is_each_groups_first_version(self):
        results = _star_finder("$*.csvpaths.:first()").query()
        assert sorted(results.uuids) == ["a-v1", "b-v1"]

    def test_index_selects_within_each_group(self):
        # alpha's versions are a-v1, a-v2; beta has only b-v1, so it has
        # no index 1
        results = _star_finder("$*.csvpaths.:index(1)").query()
        assert results.uuids == ["a-v2"]

    # no "combined with :manifest()" test in this class: a bare pointer
    # plus a bare ':manifest()' (e.g. ":last():manifest()") is always
    # exactly the two-function shape _pointer_before_manifest() matches
    # -- it is intercepted by Rule 1b in query() before ever reaching
    # _query_star_traversal, regardless of root_major being '*'. See
    # TestGlobalLoadsLedger for that already-existing, unaffected
    # behavior. TestStarTraversalGroup's own ':all():last():manifest()'
    # test below is what actually proves this class's sibling fix (the
    # traversal-guard exemption fixed 2026-08-26).

    def test_name_three_now_composes_with_traversal(self):
        # not-yet-supported sweep #9, 2026-10-20: name_three now
        # applies generically to whatever _query_star_traversal() pools/
        # groups across every named-paths group, the same shared tail
        # the literal-root case already uses. ":last()" gives each
        # group's last version (a-v2, b-v1); only b-v1 has the identity
        # "orders".
        results = _star_finder("$*.csvpaths.:last().orders").query()
        assert results.uuids == ["b-v1"]
        assert results.results[0].identity == "orders"

    def test_name_three_no_match_gives_empty(self):
        results = _star_finder("$*.csvpaths.:last().nope").query()
        assert results.results == []


class TestTraversalRootStatementResolve:
    # a name_three statement read under '*', ':regex()' or ':choice()'
    # resolves to that statement's text in the version's own group, as
    # under a literal root. Until 2026-11-12 _extract_data() passed
    # root_major to paths_manifest() and raised TypeError on resolve,
    # though the query was right. The star fixtures with statement texts.
    BY_NAME = {
        "alpha": [
            dict(
                STAR_ALPHA_MANIFEST[0],
                named_paths=["alpha orders"],
                named_paths_identities=["orders"],
            ),
            dict(
                STAR_ALPHA_MANIFEST[1],
                named_paths=["alpha x"],
                named_paths_identities=["x"],
            ),
        ],
        "beta": [
            dict(STAR_BETA_MANIFEST[0], named_paths=["beta orders", "beta one"])
        ],
    }

    def _resolve(self, reference: str) -> list:
        results = _finder(
            reference, by_name=self.BY_NAME, inputs_csvpaths_path="inputs/named_paths"
        ).resolve()
        return [(r.uuid, r.identity, r.data) for r in results.results]

    @pytest.mark.parametrize(
        "root", ["$*", '$:regex("a")', '$:choice("alpha|beta")']
    )
    @pytest.mark.parametrize(
        "tail, expected",
        [
            # alpha's last version (a-v2) has no "orders"
            (".csvpaths.:last().orders", [("b-v1", "orders", "beta orders")]),
            (
                ".csvpaths.:first().orders",
                [("a-v1", "orders", "alpha orders"), ("b-v1", "orders", "beta orders")],
            ),
            (
                ".csvpaths.:all().orders",
                [("a-v1", "orders", "alpha orders"), ("b-v1", "orders", "beta orders")],
            ),
            # a stringified index identity
            (".csvpaths.:last().1", [("b-v1", "1", "beta one")]),
            (".csvpaths.:last().nope", []),
        ],
    )
    def test_a_statement_resolves_in_its_own_group(self, root, tail, expected):
        assert self._resolve(root + tail) == expected

    def test_a_regex_root_filters_by_group(self):
        assert self._resolve('$:regex("^al").csvpaths.:all().orders') == [
            ("a-v1", "orders", "alpha orders")
        ]

    def test_a_literal_root_reads_the_same(self):
        assert self._resolve("$beta.csvpaths.:last().orders") == [
            ("b-v1", "orders", "beta orders")
        ]


class TestStarTraversalPoolNoPointerIsOptional:
    # a pointer is now optional in POOL/FLATTEN mode too (settled
    # 2026-08-19) -- previously the one place csvpaths' own star
    # traversal still required one unconditionally, an inconsistency
    # with GROUP mode's own no-pointer precedent (which already listed
    # everything per group, unreduced) and with RESULTS'/
    # FilesReferenceFinder3's star traversal (neither ever requires
    # one). Absence means every candidate across every group comes
    # back, unreduced. Unlike RESULTS/FILES, csvpaths' name_one always
    # requires SOME function as its sole path segment (no bare/literal-
    # path-only shape exists here at all, confirmed live: "$*.csvpaths."
    # with nothing after does not even parse) -- so POOL-mode-no-
    # pointer is only reachable via a field accessor or ':having()'
    # occupying that slot, not a truly empty reference.
    def test_no_pointer_with_a_field_accessor_is_poolable(self):
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        # a field with no pointer is a ledger read (2026-10-30), so the
        # ledger has to hold the same versions as the groups.
        results = _finder(
            "$*.csvpaths.:named_paths_name()",
            by_name=by_name,
            ledger=by_name["alpha"] + by_name["beta"],
        ).resolve()
        assert sorted((r.uuid, r.data) for r in results.results) == [
            ("a-v1", "alpha"),
            ("b-v1", "beta"),
        ]

    def test_previously_masked_unrecognized_function_now_raises(self):
        # a real, previously-latent bug this same fix exposed and
        # closed: the old check only ever rejected ":manifest()"/
        # ':from()'/':to()' BY NAME (a blacklist) -- any other
        # unrecognized function (e.g. ':definition()', confirmed via
        # TestGlobalLoadsLedger's own test) silently fell through
        # unrejected once "no pointer" stopped forcing a raise for an
        # unrelated reason. Now whitelist-based (only a pointer/':all()'
        # /':having()'/a field accessor are exempted), closing that gap
        # generally, not just for the one name already known about.
        with pytest.raises(ReferenceException3):
            _star_finder("$*.csvpaths.:groups()").query()


class TestStarTraversalFieldAccessor:
    # closes the gap ReferenceExpression3 needed -- a registered field-
    # accessor function can now ride alongside the pointer in '*'
    # traversal (added 2026-08-18), resolving from whichever real group
    # matched via _group_manifest_entry(), which re-derives the matched
    # group's own name/manifest from the uuid the pointer already
    # selected -- unlike RESULTS, CSVPATHS genuinely needs this, since
    # get_manifest_for_name(reference.root_major) breaks when
    # root_major is the '*' token (no group is actually named "*").
    def test_bare_pointer_with_a_field_accessor_reads_each_group(self):
        # '*' mimics grouping (compendium 4.1b): one value per group. Was
        # pooled, beta's alone.
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        results = _finder(
            "$*.csvpaths.:last():named_paths_name()", by_name=by_name
        ).resolve()
        assert sorted((r.uuid, r.data) for r in results.results) == [
            ("a-v1", "alpha"),
            ("b-v1", "beta"),
        ]

    def test_grouped_shape_with_a_field_accessor_now_works(self):
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                },
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v2",
                    "time": "2026-01-02T00:00:00+00:00",
                    "named_paths_name": "alpha",
                },
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        results = _finder(
            "$*.csvpaths.:all():last():named_paths_name()", by_name=by_name
        ).resolve()
        assert len(results.results) == 2
        assert {r.data for r in results.results} == {"alpha", "beta"}
        assert {r.uuid for r in results.results} == {"a-v2", "b-v1"}

    def test_field_accessor_combined_with_manifest_now_also_works(self):
        # ':manifest()' is now exempted from _query_star_traversal's
        # unsupported-combination check too (fixed 2026-08-26, the same
        # change that let a bare pointer/':all()' combine with it) -- so
        # this three-function chain no longer raises. resolve_kind()
        # gives a field-accessor function priority over ':manifest()'
        # when both are present in the same terminal chain (see
        # reference_3.py's own resolve_kind docstring: METADATA_FIELD is
        # checked before METADATA_FILE), so named_paths_name()'s own
        # value wins here and ':manifest()' rides along harmlessly,
        # unused -- same outcome as test_flatten_shape_with_a_field_
        # accessor_now_works above, just proving the extra function does
        # not change it.
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                    "named_paths_name": "beta",
                }
            ],
        }
        # with ':manifest()' this is a ledger read (2026-10-30), so the
        # ledger has to hold the same versions as the groups.
        results = _finder(
            "$*.csvpaths.:last():named_paths_name():manifest()",
            by_name=by_name,
            ledger=by_name["alpha"] + by_name["beta"],
            inputs_csvpaths_path="named_paths",
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "b-v1"
        assert results.results[0].data == "beta"

    def test_definition_sourced_field_reads_the_matched_groups_own_config(self):
        # :scripts() (SOURCE == "definition") is the other branch
        # _group_manifest_entry() serves -- it needs the matched GROUP
        # NAME, not just its manifest entry, to call describer.get_
        # config(name). Proves each group's own definition.json is read,
        # not one group's for both, by giving each group a different
        # "scripts" config. One result per group (compendium 4.1b).
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                }
            ],
            "beta": [
                {
                    "group_file_path": "named_paths/beta/group.csvpath",
                    "uuid": "b-v1",
                    "time": "2026-01-03T00:00:00+00:00",
                }
            ],
        }
        definitions_by_name = {
            "alpha": {"scripts": {"on_complete_all": "alpha_notify.py"}},
            "beta": {"scripts": {"on_complete_all": "beta_notify.py"}},
        }
        # one result per group with no version: definition.json is not
        # versioned (2026-11-10). Read through ':last()' until then.
        results = _finder(
            "$*.csvpaths.:scripts()",
            by_name=by_name,
            definitions_by_name=definitions_by_name,
        ).resolve()
        assert [(r.uuid, r.data["on_complete_all"]) for r in results.results] == [
            (None, "alpha_notify.py"),
            (None, "beta_notify.py"),
        ]

    def test_an_argument_on_the_field_accessor_is_a_gate(self):
        # changed 2026-11-05 (finding A). This raised when '*' traversal
        # had no GATE mechanism; before that guard, the argument was
        # silently ignored. Now an argued version-entry field filters:
        # no version is named "x", so nothing comes back.
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                    "named_paths_name": "alpha",
                }
            ],
        }
        results = _finder(
            '$*.csvpaths.:last():named_paths_name("x")', by_name=by_name
        ).query()
        assert results.results == []
        results = _finder(
            '$*.csvpaths.:last():named_paths_name("alpha")', by_name=by_name
        ).query()
        assert results.uuids == ["a-v1"]

    def test_a_templated_key_functions_own_argument_is_not_rejected(self):
        # the guard above must not catch EVERY argued field accessor --
        # :destination_address()'s own KEY has a "{}" placeholder,
        # genuinely consumed by _apply_key_arg() at resolve() time, not
        # silently ignored. Confirmed live before this exemption
        # existed that the broader guard wrongly rejected this (and
        # six sibling definition-sourced sub-field accessors) too.
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                }
            ],
        }
        definitions_by_name = {
            "alpha": {"destinations": {"myd": {"address": "ftp.example.com"}}}
        }
        results = _finder(
            '$*.csvpaths.:destination_address("myd")',
            by_name=by_name,
            definitions_by_name=definitions_by_name,
        ).resolve()
        assert [r.data for r in results.results] == ["ftp.example.com"]


class TestGroupManifestEntry:
    # _group_manifest_entry() -- added 2026-08-18 alongside the field-
    # accessor exemption above, so the METADATA_FIELD manifest-sourced
    # branch can re-derive which real group a star-traversal result came
    # from (the definition-sourced fields used it too until 2026-11-10,
    # when they became a definition chain), tested directly here
    # rather than only indirectly through resolve().
    def test_star_root_major_finds_the_correct_group(self):
        by_name = {
            "alpha": [{"group_file_path": "x", "uuid": "a-v1"}],
            "beta": [{"group_file_path": "y", "uuid": "b-v1"}],
        }
        finder = _finder("$*.csvpaths.:last()", by_name=by_name)
        name, entry = finder._group_manifest_entry(Star3(), "b-v1")
        assert name == "beta"
        assert entry["uuid"] == "b-v1"

    def test_regex_root_major_finds_the_correct_group(self):
        # added 2026-08-27 -- a :regex() root_major spans potentially
        # more than one group too (ReferenceFinder3._is_traversal_root()),
        # same reasoning as the '*' case above.
        from csvpath.references.reference_3 import FunctionCall3

        by_name = {
            "acme_group": [{"group_file_path": "x", "uuid": "a-v1"}],
            "abba_group": [{"group_file_path": "y", "uuid": "b-v1"}],
        }
        finder = _finder("$acme_group.csvpaths.:last()", by_name=by_name)
        name, entry = finder._group_manifest_entry(
            FunctionCall3(name="regex", arg="abba_.*"), "b-v1"
        )
        assert name == "abba_group"
        assert entry["uuid"] == "b-v1"

    def test_star_root_major_with_unknown_uuid_gives_none_none(self):
        by_name = {"alpha": [{"group_file_path": "x", "uuid": "a-v1"}]}
        finder = _finder("$*.csvpaths.:last()", by_name=by_name)
        name, entry = finder._group_manifest_entry(Star3(), "missing-uuid")
        assert name is None
        assert entry is None

    def test_literal_root_major_looks_up_directly_no_group_search(self):
        # a literal root_major never needs to search every group -- this
        # mirrors what every non-star call site did inline before this
        # helper existed.
        finder = _finder("$acme.csvpaths.:last()")
        name, entry = finder._group_manifest_entry("acme", "v1-uuid")
        assert name == "acme"
        assert entry["uuid"] == "v1-uuid"


def _root_group_entry(name: str, uuid: str, day: int, identities: list) -> dict:
    return {
        "group_file_path": f"named_paths/{name}/group.csvpath",
        "uuid": uuid,
        "time": f"2026-01-0{day}T00:00:00+00:00",
        "named_paths_name": name,
        "named_paths_identities": identities,
    }


#
# finding I fixture: alpha has three versions, beta two, gamma one. Only
# alpha's v1 and v2 and beta's v1 have "checks", so a group's last version
# and its last version having "checks" differ. beta's v2 is the most
# recent version overall. The ledger holds every version, in arrival
# order, for the ':manifest()' forms that still pool.
#
ROOT_GROUP_BY_NAME = {
    "alpha": [
        _root_group_entry("alpha", "a-v1", 1, ["checks"]),
        _root_group_entry("alpha", "a-v2", 3, ["checks"]),
        _root_group_entry("alpha", "a-v3", 5, []),
    ],
    "beta": [
        _root_group_entry("beta", "b-v1", 2, ["checks"]),
        _root_group_entry("beta", "b-v2", 6, []),
    ],
    "gamma": [_root_group_entry("gamma", "g-v1", 4, [])],
}
ROOT_GROUP_LEDGER = sorted(
    (e for entries in ROOT_GROUP_BY_NAME.values() for e in entries),
    key=lambda e: e["time"],
)


def _root_group_finder(reference: str) -> CsvpathsReferenceFinder3:
    return _finder(
        reference,
        by_name=ROOT_GROUP_BY_NAME,
        ledger=ROOT_GROUP_LEDGER,
        inputs_csvpaths_path="named_paths",
    )


def _gate_entry(name: str, uuid: str, day: int, template: str, **extra) -> dict:
    entry = {
        "named_paths_name": name,
        "group_file_path": f"named_paths/{name}/group.csvpaths",
        "uuid": uuid,
        "time": f"2026-01-0{day}T00:00:00+00:00",
        "template": template,
    }
    entry.update(extra)
    return entry


#
# finding A fixture. acme's four versions have templates "", ":1/:2", ":1"
# and "", so a1 and a4 have none: a range, a gate and a pointer give
# different answers depending on which goes first. beta has b1 ("") and
# b2 (":x"). gone was deleted: its g1 is only in the root ledger, marked
# deleted. Ledger order is arrival order.
#
GATE_BY_NAME = {
    "acme": [
        _gate_entry("acme", "a1", 1, ""),
        _gate_entry("acme", "a2", 3, ":1/:2"),
        _gate_entry("acme", "a3", 5, ":1"),
        _gate_entry("acme", "a4", 7, ""),
    ],
    "beta": [
        _gate_entry("beta", "b1", 2, ""),
        _gate_entry("beta", "b2", 6, ":x"),
    ],
}
GATE_LEDGER = sorted(
    [
        *(dict(e, lifecycle="active") for es in GATE_BY_NAME.values() for e in es),
        _gate_entry("gone", "g1", 4, ":y", lifecycle="deleted"),
    ],
    key=lambda e: e["time"],
)


def _gate_finder(reference: str) -> CsvpathsReferenceFinder3:
    return _finder(
        reference,
        by_name={name: [dict(e) for e in es] for name, es in GATE_BY_NAME.items()},
        ledger=[dict(e) for e in GATE_LEDGER],
        definitions_by_name={
            "acme": {"destinations": {"myd": {"address": "ftp.acme.example"}}},
            "beta": {},
        },
        inputs_csvpaths_path="named_paths",
    )


class TestCsvpathsGates:
    # finding A (David 2026-10-29, built 2026-11-05): an argued version-
    # entry field is a GATE in CSVPATHS too, as in FILES and RESULTS. Gates
    # are ANDed in any written order (compendium 6.1, 6.35); a range comes
    # first (6.28), then the gates, then the pointer picks from what is
    # left. A gate never supplies the resolve value (finding D). Every
    # reference below used to raise "does not take an argument".
    @pytest.mark.parametrize(
        "reference, expected",
        [
            # the pointer picks from what the gate leaves, in either order:
            # acme's versions with a template are a2 and a3
            ("$acme.csvpaths.:last():template(:has_value())", ["a3"]),
            ("$acme.csvpaths.:template(:has_value()):last()", ["a3"]),
            ("$acme.csvpaths.:first():template(:has_value())", ["a2"]),
            ("$acme.csvpaths.:last():template(:does_not_have_value())", ["a4"]),
            # range first: a1, a2, then the gate: a2. Gate first would be
            # a2, a3, then the range: a2, a3, and :last() a3
            ("$acme.csvpaths.:from(0):to(1):template(:has_value()):last()", ["a2"]),
            ("$acme.csvpaths.:template(:has_value()):from(0):to(1):last()", ["a2"]),
            # gates are ANDed
            (
                "$acme.csvpaths.:last():template(:has_value())"
                ':named_paths_name("acme")',
                ["a3"],
            ),
            (
                "$acme.csvpaths.:last():template(:has_value())"
                ':named_paths_name("x")',
                [],
            ),
            (
                '$acme.csvpaths.:all():named_paths_name("acme")',
                ["a1", "a2", "a3", "a4"],
            ),
            ('$acme.csvpaths.:all():named_paths_name("beta")', []),
            # a version set gates on each version's own template too, not
            # only a pointer (David, 2026-11-11). These used to raise "does
            # not take an argument"
            ("$acme.csvpaths.:all():template(:has_value())", ["a2", "a3"]),
            (
                "$acme.csvpaths.:all():template(:does_not_have_value())",
                ["a1", "a4"],
            ),
            ("$acme.csvpaths.:from(0):to(3):template(:has_value())", ["a2", "a3"]),
            # range first: a1, a2, then the gate
            ("$acme.csvpaths.:from(0):to(1):template(:has_value())", ["a2"]),
            ("$acme.csvpaths.:template(:has_value()):from(0):to(1)", ["a2"]),
            (
                "$acme.csvpaths.:manifest():template(:has_value()):uuid()",
                ["a2", "a3"],
            ),
        ],
    )
    def test_a_literal_root_gate_filters(self, reference, expected):
        assert _gate_finder(reference).query().uuids == expected

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # one per group (compendium 4.1b), each after its own gate
            ("$*.csvpaths.:last():template(:has_value())", ["a3", "b2"]),
            ("$*.csvpaths.:all():first():template(:has_value())", ["a2", "b2"]),
            ('$*.csvpaths.:last():named_paths_name("beta")', ["b2"]),
            # no pointer: the live groups' versions, in time order
            ('$*.csvpaths.:named_paths_name("beta")', ["b1", "b2"]),
            # the root ledger, the deleted g1 included
            ('$*.csvpaths.:manifest():named_paths_name("gone")', ["g1"]),
            ('$*.csvpaths.:manifest():last():named_paths_name("acme")', ["a4"]),
            ('$*.csvpaths.:manifest():named_paths_name("acme"):last()', ["a4"]),
            ("$*.csvpaths.:manifest():last():template(:has_value())", ["b2"]),
            (
                '$:regex(/^(acme|gone)$/).csvpaths.:manifest():template(:has_value())'
                ":last()",
                ["a3"],
            ),
            # a version set, per group and on the ledger (2026-11-11)
            ("$*.csvpaths.:all():template(:has_value())", ["a2", "a3", "b2"]),
            (
                "$*.csvpaths.:manifest():template(:has_value())",
                ["a2", "g1", "a3", "b2"],
            ),
        ],
    )
    def test_a_star_gate_filters(self, reference, expected):
        assert _gate_finder(reference).query().uuids == expected

    def test_a_ledger_gate_reads_a_deleted_versions_ledger_entry(self):
        # g1's template is only in its ledger entry. In ledger order the
        # versions with a template are a2, g1, a3 and b2.
        results = _gate_finder(
            "$*.csvpaths.:manifest():template(:has_value()):index(1)"
        ).query()
        assert results.uuids == ["g1"]

    def test_a_gate_supplies_no_value(self):
        # finding D: with only gates, resolve gives what the reference
        # gives without them
        gated = _gate_finder("$acme.csvpaths.:last():template(:has_value())")
        plain = _gate_finder("$acme.csvpaths.:index(2)")
        assert [r.data for r in gated.resolve().results] == [
            r.data for r in plain.resolve().results
        ]
        ledger = _gate_finder('$*.csvpaths.:manifest():named_paths_name("gone")')
        assert [r.data["uuid"] for r in ledger.resolve().results] == ["g1"]

    @pytest.mark.parametrize(
        "reference",
        [
            "$acme.csvpaths.:last():template(:has_value()):uuid()",
            "$acme.csvpaths.:last():uuid():template(:has_value())",
        ],
    )
    def test_the_value_comes_from_the_unargued_field_in_either_order(
        self, reference
    ):
        assert [r.data for r in _gate_finder(reference).resolve().results] == ["a3"]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$acme.csvpaths.:all():template(:has_value()):uuid()", ["a2", "a3"]),
            (
                "$acme.csvpaths.:all():template(:has_value()):template()",
                [":1/:2", ":1"],
            ),
            (
                "$acme.csvpaths.:from(0):to(3):template():template(:has_value())",
                [":1/:2", ":1"],
            ),
            (
                "$acme.csvpaths.:manifest():template(:has_value()):template()",
                [":1/:2", ":1"],
            ),
            (
                "$*.csvpaths.:all():template(:has_value()):uuid()",
                ["a2", "a3", "b2"],
            ),
        ],
    )
    def test_a_version_set_gate_takes_its_value_from_the_unargued_field(
        self, reference, expected
    ):
        # each version's own template, read beside :all(), a range or
        # :manifest() (2026-11-11)
        results = _gate_finder(reference).resolve().results
        assert [r.data for r in results] == expected

    def test_the_ledger_value_comes_from_the_unargued_field(self):
        results = _gate_finder(
            '$*.csvpaths.:manifest():named_paths_name("gone"):uuid()'
        ).resolve()
        assert [r.data for r in results.results] == ["g1"]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ('$*.csvpaths.:manifest():lifecycle("deleted")', ["g1"]),
            ('$*.csvpaths.:manifest():lifecycle("deleted"):last()', ["g1"]),
            (
                '$*.csvpaths.:manifest():lifecycle("active")',
                ["a1", "b1", "a2", "a3", "b2", "a4"],
            ),
            ('$*.csvpaths.:manifest():last():lifecycle("active")', ["a4"]),
            # a live group's per-name entries have no lifecycle: the
            # ledger supplies it
            ('$acme.csvpaths.:last():lifecycle("active")', ["a4"]),
            ('$*.csvpaths.:lifecycle("deleted")', []),
        ],
    )
    def test_the_lifecycle_gate(self, reference, expected):
        # ':lifecycle()' (2026-11-05) through the gate mechanism
        assert _gate_finder(reference).query().uuids == expected

    def test_a_definition_field_beside_a_gate_raises(self):
        # a gate selects versions, and definition.json has none
        # (2026-11-10). Read the definition beside the gate until then.
        with pytest.raises(ReferenceException3) as error:
            _gate_finder(
                '$acme.csvpaths.:last():named_paths_name("acme")'
                ':destination_address("myd")'
            ).query()
        assert "definition.json, which is not versioned" in str(error.value)

    @pytest.mark.parametrize(
        "reference",
        [
            # (':all():template(:has_value())' and the ledger's
            # ':manifest():template(:has_value())' were here until they
            # became gates, 2026-11-11.) Another datatype's field
            # (2026-11-05): under '*' these read None and filtered
            # everything out silently after #522.
            # (':status()' was one of these until it became a CSVPATHS
            # field, 2026-11-06.)
            '$*.csvpaths.:type("csv")',
            '$*.csvpaths.:last():error_count(0)',
            '$*.csvpaths.:manifest():named_file_name("acme")',
        ],
    )
    def test_an_argument_that_is_not_a_gate_still_raises(self, reference):
        with pytest.raises(ReferenceException3):
            _gate_finder(reference).query()


#
# ':status()' fixture (2026-11-06). The loads ledger holds a status per load:
# "complete", or "unchanged" for a reload of a group whose file had not
# changed. acme's a2 was reloaded unchanged: a2-reload is its own ledger
# entry, linked by version_uuid, and not a version in acme's manifest. b1
# was written before loads had a status, so it has none.
#
STATUS_LEDGER = sorted(
    [
        *(
            dict(e, status="complete", lifecycle="active")
            for es in GATE_BY_NAME.values()
            for e in es
            if e["uuid"] != "b1"
        ),
        dict(GATE_BY_NAME["beta"][0], lifecycle="active"),
        dict(
            _gate_entry("acme", "a2-reload", 4, ":1/:2"),
            status="unchanged",
            lifecycle="active",
            version_uuid="a2",
        ),
    ],
    key=lambda e: e["time"],
)


def _status_finder(reference: str) -> CsvpathsReferenceFinder3:
    return _finder(
        reference,
        by_name={name: [dict(e) for e in es] for name, es in GATE_BY_NAME.items()},
        ledger=[dict(e) for e in STATUS_LEDGER],
        inputs_csvpaths_path="named_paths",
    )


class TestStarRangesAndTimeWindows:
    # 2026-11-06: under '*', CSVPATHS rejected a range ("does not support
    # :from() combined with '*' traversal", a bug -- David) and silently
    # ignored a bare time window, giving every version. Both now narrow as
    # at the literal root: per named-paths group, since an index range is
    # a multi-valued pointer (compendium 4.1b), or on the pooled ledger
    # with ':manifest()'. Range first, then gates, then the pointer (6.28).
    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$*.csvpaths.:from(0):to(1)", ["a1", "a2", "b1", "b2"]),
            ("$*.csvpaths.:from(0):to(1):last()", ["a2", "b2"]),
            ("$*.csvpaths.:all():from(0):to(0)", ["a1", "b1"]),
            ("$*.csvpaths.:from(0):to(1):template(:has_value()):last()", ["a2", "b2"]),
            # a date range is a match on each version's time: no grouping
            # needed, so the pooled list in time order
            ('$*.csvpaths.:from(:date("2026-01-03"))', ["a2", "a3", "b2", "a4"]),
            ('$*.csvpaths.:from(:date("2026-01-03")):last()', ["a4", "b2"]),
            # the ledger, in ledger order: a1, b1, a2, g1, ...
            ("$*.csvpaths.:manifest():from(0):to(1)", ["a1", "b1"]),
            (
                '$*.csvpaths.:manifest():from(:date("2026-01-03"))'
                ':to(:date("2026-01-05"))',
                ["a2", "g1", "a3"],
            ),
            # every fixture version is from January 2026
            ("$*.csvpaths.:yesterday()", []),
            ("$*.csvpaths.:yesterday():last()", []),
            ("$*.csvpaths.:manifest():yesterday()", []),
        ],
    )
    def test_star_narrows_like_the_literal_root(self, reference, expected):
        assert _gate_finder(reference).query().uuids == expected

    def test_each_group_matches_its_literal_root(self):
        for reference in ("{}.csvpaths.:from(0):to(1)", "{}.csvpaths.:from(1):last()"):
            star = _gate_finder(reference.format("$*")).query().uuids
            each = [
                u
                for name in ("$acme", "$beta")
                for u in _gate_finder(reference.format(name)).query().uuids
            ]
            assert star == each, reference


class TestCsvpathsStatus:
    # ':status()' for CSVPATHS (David, 2026-11-06): a ledger-only field, as
    # in FILES, read and gated through the same machinery as every other
    # field (finding A). It used to raise "is not legal at name_one for
    # csvpaths".
    def test_the_field_reads_every_ledger_entry(self):
        results = _status_finder("$*.csvpaths.:manifest():status()").resolve()
        assert [(r.uuid, r.data) for r in results.results] == [
            ("a1", "complete"),
            ("b1", None),
            ("a2", "complete"),
            ("a2-reload", "unchanged"),
            ("a3", "complete"),
            ("b2", "complete"),
            ("a4", "complete"),
        ]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ('$*.csvpaths.:manifest():status("unchanged")', ["a2-reload"]),
            ('$*.csvpaths.:manifest():status("complete"):last()', ["a4"]),
            ('$*.csvpaths.:manifest():last():status("unchanged")', ["a2-reload"]),
            # an entry with no status matches neither value
            ('$:regex(/^beta$/).csvpaths.:manifest():status("complete")', ["b2"]),
            # a version reads its own load's ledger entry; an unchanged
            # reload is not a version, so only the ledger set reaches it
            ('$acme.csvpaths.:all():status("complete")', ["a1", "a2", "a3", "a4"]),
            ('$acme.csvpaths.:all():status("unchanged")', []),
            ('$*.csvpaths.:last():status("complete")', ["a4", "b2"]),
        ],
    )
    def test_the_gate(self, reference, expected):
        assert _status_finder(reference).query().uuids == expected

    def test_a_version_reads_its_own_status(self):
        results = _status_finder("$acme.csvpaths.:last():status()").resolve()
        assert [r.data for r in results.results] == ["complete"]

    def test_status_with_lifecycle(self):
        results = _status_finder(
            '$*.csvpaths.:manifest():status("complete"):lifecycle("active")'
        ).query()
        assert results.uuids == ["a1", "a2", "a3", "b2", "a4"]


class TestStarRootGroups:
    # finding I (David, 2026-10-30 and 2026-11-03; compendium 4.1b): a
    # '*' root mimics grouping. A pointer applies within each named-paths
    # group, one result per group. It used to pool every group's versions
    # and give one result in total. ':manifest()' without ':all()' names
    # the global loads ledger and still pools.
    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$*.csvpaths.:last()", ["a-v3", "b-v2", "g-v1"]),
            ("$*.csvpaths.:first()", ["a-v1", "b-v1", "g-v1"]),
            ("$*.csvpaths.:index(-1)", ["a-v3", "b-v2", "g-v1"]),
            ("$*.csvpaths.:index(1)", ["a-v2", "b-v2"]),
            # the same as ':all()', which is now redundant but permitted
            ("$*.csvpaths.:all():last()", ["a-v3", "b-v2", "g-v1"]),
        ],
    )
    def test_a_pointer_gives_one_result_per_group(self, reference, expected):
        assert sorted(_root_group_finder(reference).query().uuids) == expected

    def test_having_then_a_pointer_is_per_group(self):
        # NRE "Find last version containing my_validations for all
        # named-paths groups": gamma has no version with "checks"
        results = _root_group_finder(
            '$*.csvpaths.:having("checks"):index(-1)'
        ).query()
        assert sorted(results.uuids) == ["a-v2", "b-v1"]

    def test_an_identity_after_the_pointer_is_per_group(self):
        # NRE "For all named-paths groups, find my_validations in any
        # named-paths group's last version": no group's last version has
        # "checks", and alpha's v2 is not its last
        results = _root_group_finder("$*.csvpaths.:last().checks").query()
        assert results.results == []
        results = _root_group_finder("$*.csvpaths.:first().checks").query()
        assert sorted(results.uuids) == ["a-v1", "b-v1"]
        assert {r.identity for r in results.results} == {"checks"}

    def test_a_field_after_the_pointer_reads_each_group(self):
        results = _root_group_finder("$*.csvpaths.:last():uuid()").resolve()
        assert sorted(r.data for r in results.results) == ["a-v3", "b-v2", "g-v1"]

    def test_a_regex_root_groups_the_same_way(self):
        results = _root_group_finder("$:regex(/^(alpha|beta)$/).csvpaths.:last()")
        assert sorted(results.query().uuids) == ["a-v3", "b-v2"]

    def test_no_pointer_keeps_arrival_order(self):
        # nothing to reduce per group, so the pooled list in time order
        results = _root_group_finder("$*.csvpaths.:uuid()").query()
        assert results.uuids == ["a-v1", "b-v1", "a-v2", "g-v1", "a-v3", "b-v2"]

    def test_the_ledger_still_pools(self):
        # ':manifest()' names the global loads ledger, the logical set
        # across every group: its last entry is beta's v2, alone
        results = _root_group_finder("$*.csvpaths.:manifest():last()").query()
        assert results.uuids == ["b-v2"]


class TestStarTraversalGroup:
    # ':all()' present in the combined name_one chain -- the pointer is
    # applied independently within each group's own manifest, one
    # result per group.
    def test_all_with_last_gives_one_result_per_group(self):
        results = _star_finder("$*.csvpaths.:all():last()").query()
        assert len(results.results) == 2
        assert set(results.uuids) == {"a-v2", "b-v1"}

    def test_all_with_first_gives_each_groups_earliest_version(self):
        results = _star_finder("$*.csvpaths.:all():first()").query()
        assert len(results.results) == 2
        assert set(results.uuids) == {"a-v1", "b-v1"}

    def test_all_with_no_pointer_gives_every_version_unreduced(self):
        # extends csvpaths' own existing single-group precedent (bare
        # :all() with no pointer -- test_bare_all_returns_every_version
        # above) across every group, rather than deduping to anything.
        results = _star_finder("$*.csvpaths.:all()").query()
        assert len(results.results) == 3
        assert set(results.uuids) == {"a-v1", "a-v2", "b-v1"}

    def test_all_with_last_and_manifest_gives_each_groups_own_manifest_entry(self):
        # previously unsupported (raised); fixed 2026-08-26 -- see
        # TestStarTraversalFlatten's own manifest test for the FLATTEN-
        # mode sibling of this fix. Proves the GROUP-mode reduction
        # (one version per group) and the manifest-entry lookup compose
        # correctly together, not just each in isolation.
        results = _star_finder("$*.csvpaths.:all():last():manifest()").resolve()
        assert len(results.results) == 2
        data_by_uuid = {r.uuid: r.data for r in results.results}
        assert data_by_uuid == {
            "a-v2": STAR_ALPHA_MANIFEST[1],
            "b-v1": STAR_BETA_MANIFEST[0],
        }


class TestStarTraversalHaving:
    # ':having("identity")' combined with '*' traversal -- added
    # 2026-08-18, alongside RESULTS' own ':flatten()' fix. Closes a
    # real, previously-latent bug, not just a missing feature: before
    # this fix ':having()' was never checked for at all in
    # _query_star_traversal -- neither rejected as unsupported NOR
    # applied -- so it was silently DROPPED (confirmed live before
    # writing these: "$*.csvpaths.:all():having('orders')" returned
    # EVERY group's every version, unfiltered, not just the matching
    # ones).
    HAVING_BY_NAME = {
        "alpha": [
            {
                "group_file_path": "named_paths/alpha/group.csvpath",
                "uuid": "a-v1",
                "time": "2026-01-01T00:00:00+00:00",
                "named_paths_identities": ["orders"],
                "named_paths_name": "alpha",
            },
            {
                "group_file_path": "named_paths/alpha/group.csvpath",
                "uuid": "a-v2",
                "time": "2026-01-02T00:00:00+00:00",
                "named_paths_identities": ["other"],
                "named_paths_name": "alpha",
            },
        ],
        "beta": [
            {
                "group_file_path": "named_paths/beta/group.csvpath",
                "uuid": "b-v1",
                "time": "2026-01-03T00:00:00+00:00",
                "named_paths_identities": ["other"],
                "named_paths_name": "beta",
            }
        ],
    }

    def test_grouped_having_filters_out_non_matching_versions(self):
        # the actual bug this closes: without the fix, this returned all
        # three versions, unfiltered -- only a-v1 actually has "orders".
        results = _finder(
            "$*.csvpaths.:all():having(\"orders\")", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.uuids == ["a-v1"]

    def test_grouped_having_with_pointer_gives_one_per_matching_group(self):
        # beta has no version with "orders" at all -- it contributes
        # nothing, not an empty/None placeholder.
        results = _finder(
            "$*.csvpaths.:having(\"orders\"):all():last()",
            by_name=self.HAVING_BY_NAME,
        ).query()
        assert results.uuids == ["a-v1"]

    def test_flatten_having_pools_filtered_versions_across_groups(self):
        # not grouped (no ':all()') -- filtered pool across every group,
        # reduced by the pointer, same as the ungrouped/flatten mode
        # already does for the unfiltered case.
        results = _finder(
            "$*.csvpaths.:having(\"orders\"):last()", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.uuids == ["a-v1"]

    def test_having_combined_with_a_field_accessor_also_works(self):
        results = _finder(
            "$*.csvpaths.:having(\"orders\"):all():last():named_paths_name()",
            by_name=self.HAVING_BY_NAME,
        ).resolve()
        assert len(results.results) == 1
        assert results.results[0].uuid == "a-v1"
        assert results.results[0].data == "alpha"

    def test_having_with_no_matching_version_anywhere_is_empty(self):
        results = _finder(
            "$*.csvpaths.:all():having(\"nope\")", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.results == []

    def test_having_rejects_a_nested_function_argument(self):
        # ':having()'s own ARG_TYPES widened 2026-10-18 to also accept
        # a nested function (RESULTS' own need) -- CSVPATHS has no
        # per-statement field to match against, so it still only
        # accepts a plain identity string here too, in '*' traversal.
        with pytest.raises(ReferenceException3):
            _finder(
                '$*.csvpaths.:all():having(:uuid("x"))',
                by_name=self.HAVING_BY_NAME,
            ).query()

    def test_bare_having_alone_with_no_pointer_lists_matching_versions(self):
        # a pointer is optional everywhere in csvpaths' star traversal
        # now (settled 2026-08-19, closing the one place it was still
        # required unconditionally) -- a bare ':having()' with no
        # pointer and no ':all()' means "every matching version, pooled
        # across every group, unreduced," the same POOL-mode-no-pointer
        # meaning a bare pointer-less reference now has too.
        results = _finder(
            "$*.csvpaths.:having(\"orders\")", by_name=self.HAVING_BY_NAME
        ).query()
        assert results.uuids == ["a-v1"]

    def test_list_having_matches_any_of_these_identities(self):
        # widened 2026-10-18 -- "not-real" matches nothing, "orders"
        # matches a-v1 only (a-v2/b-v1 both have "other", not in the
        # list).
        results = _finder(
            "$*.csvpaths.:all():having(@identities)",
            by_name=self.HAVING_BY_NAME,
            variables={"identities": ["orders", "not-real"]},
        ).query()
        assert results.uuids == ["a-v1"]


class TestDefinitionFunction:
    # ":definition()" mirrors ":manifest()" exactly -- same bare, sole-
    # content shape, same query()/_extract_data() routing -- except
    # definition.json is genuinely optional, so resolving one that was
    # never written gives None rather than raising.
    def test_query_returns_the_definition_path_with_no_uuid(self):
        results = _finder("$acme.csvpaths.:definition()").query()
        assert results.files == [pathu.resep(f"{GROUP_HOME}/definition.json")]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_definition_files_raw_bytes(self, tmp_path):
        content = b'{"_config": {}}'
        home = tmp_path / "acme"
        home.mkdir()
        (home / "definition.json").write_bytes(content)
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(
            string="$acme.csvpaths.:definition()", csvpaths=csvpaths
        )
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_resolve_gives_none_when_never_configured(self, tmp_path):
        home = tmp_path / "acme"
        home.mkdir()
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(
            string="$acme.csvpaths.:definition()", csvpaths=csvpaths
        )
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data is None


class TestReadmeFunction:
    # ":readme()" -- added 2026-09-21, same bare/sole-content shape as
    # ":definition()" above, but README.md is generated by the system by
    # default (compendium 6.12), so absence is the unusual case, not the
    # normal one -- still resolves to None rather than raising, same
    # treatment as every other genuinely-missing well-known file.
    def test_query_returns_the_readme_path_with_no_uuid(self):
        results = _finder("$acme.csvpaths.:readme()").query()
        assert results.files == [pathu.resep(f"{GROUP_HOME}/README.md")]
        assert results.results[0].uuid is None

    def test_resolve_reads_the_readmes_raw_bytes(self, tmp_path):
        content = b"# acme\n\nSome notes about this named-paths group.\n"
        home = tmp_path / "acme"
        home.mkdir()
        (home / "README.md").write_bytes(content)
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(string="$acme.csvpaths.:readme()", csvpaths=csvpaths)
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data == content

    def test_resolve_gives_none_when_never_generated(self, tmp_path):
        home = tmp_path / "acme"
        home.mkdir()
        csvpaths = _FakeCsvPaths(_FakePathsManager(ACME_MANIFEST, home=str(home)))
        ref = ReferenceParser3(string="$acme.csvpaths.:readme()", csvpaths=csvpaths)
        finder = CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)
        results = finder.resolve()
        assert results.results[0].data is None

    def test_readme_combined_with_a_pointer_is_rejected(self):
        # compendium 6.12/6.19: "you cannot combine version selection
        # with the ':readme()' function in name_one." Fixed 2026-09-22
        # -- used to silently no-op (':readme()' simply ignored, this
        # resolving as if it were not there at all); now raises via
        # _name_one_contains_function()'s own explicit guard, the same
        # rejection FILES gets for free through path-segment validation.
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:last():readme()").query()

    def test_readme_before_a_pointer_is_also_rejected(self):
        # order-insensitive, same as the check itself (it scans the
        # whole combined chain, not just the trailing functions).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:readme():last()").query()


RICH_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v0-uuid",
        "named_paths": ["stmt text A", "stmt text B"],
        "named_paths_identities": ["company_names", "1"],
        "named_paths_count": 2,
        "time": "2026-01-01T00:00:00+00:00",
        "fingerprint": "aaaa",
        "source_path": "/staging/acme",
        "named_paths_home": GROUP_HOME,
    },
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v1-uuid",
        "named_paths": ["stmt text C"],
        "named_paths_identities": ["0"],
        "named_paths_count": 1,
        "time": "2026-02-01T00:00:00+00:00",
        "fingerprint": "bbbb",
        "source_path": "/staging/acme",
        "named_paths_home": GROUP_HOME,
    },
]


class TestFieldAccessorFunctions:
    # generalized field-accessor wiring (see manifest_field_functions_
    # proposal.md, Part A/B): each of these rides in name_one's own
    # combined chain exactly where :manifest() already rides, either
    # alone (every version, unreduced) or beside a version pointer (one
    # reduced version) -- but extracts one key from the matched entry
    # instead of the whole thing.
    def test_bare_uuid_with_no_pointer_gives_every_versions_uuid(self):
        results = _finder("$acme.csvpaths.:uuid()", RICH_MANIFEST).resolve()
        assert [r.data for r in results.results] == ["v0-uuid", "v1-uuid"]

    def test_uuid_beside_a_pointer_gives_the_one_matched_value(self):
        results = _finder("$acme.csvpaths.:last():uuid()", RICH_MANIFEST).resolve()
        assert results.results[0].data == "v1-uuid"

    def test_time(self):
        results = _finder("$acme.csvpaths.:first():time()", RICH_MANIFEST).resolve()
        assert results.results[0].data == "2026-01-01T00:00:00+00:00"

    def test_fingerprint(self):
        results = _finder(
            "$acme.csvpaths.:first():fingerprint()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == "aaaa"

    def test_group_home(self):
        # :home() split 2026-08-26 -- CSVPATHS' own share of the old
        # field-read job is now :group_home() (:home() itself was
        # retired 2026-11-03).
        results = _finder(
            "$acme.csvpaths.:first():group_home()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == GROUP_HOME

    def test_origin_reads_the_source_path_key(self):
        results = _finder("$acme.csvpaths.:first():origin()", RICH_MANIFEST).resolve()
        assert results.results[0].data == "/staging/acme"

    def test_named_paths_identities(self):
        results = _finder(
            "$acme.csvpaths.:first():named_paths_identities()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == ["company_names", "1"]

    def test_named_paths_count(self):
        results = _finder(
            "$acme.csvpaths.:last():named_paths_count()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == 1

    def test_field_function_combined_with_all_gives_every_version(self):
        results = _finder(
            "$acme.csvpaths.:all():named_paths_count()", RICH_MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == [2, 1]

    def test_group_file(self):
        results = _finder(
            "$acme.csvpaths.:first():group_file()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == GROUP_FILE_PATH

    def test_named_paths(self):
        results = _finder(
            "$acme.csvpaths.:first():named_paths()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == ["stmt text A", "stmt text B"]

    def test_archive(self):
        manifest = [
            {**RICH_MANIFEST[0], "archive_name": "archive-2026"},
        ]
        results = _finder("$acme.csvpaths.:first():archive()", manifest).resolve()
        assert results.results[0].data == "archive-2026"

    def test_group_manifest_falls_back_to_the_global_ledger(self):
        # group_manifest_3.py's KEY is empty -- the named-paths group's
        # own manifest never has this field, only the global ledger does
        # (see the shared LEDGER_KEY fallback mechanism this proves).
        ledger = [{"uuid": "v1-uuid", "paths_manifest": "named_paths/acme/manifest.json"}]
        results = _finder(
            "$acme.csvpaths.:last():group_manifest()", RICH_MANIFEST, ledger=ledger
        ).resolve()
        assert results.results[0].data == "named_paths/acme/manifest.json"

    def test_function_not_legal_here_is_rejected_not_silently_degraded(self):
        # :mark()'s own DATATYPES is FILES-only, and it has no POSITIONS
        # entry for csvpaths at all -- added 2026-08-14: this now raises
        # via ReferenceFinder3._check_position(), called from
        # _resolve_versions(), instead of silently reaching
        # _extract_data() and degrading to None on a KEY lookup with no
        # CSVPATHS entry (the old, undetected gap this test used to
        # lock in).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:first():mark()", RICH_MANIFEST).query()

    def test_username_host_fall_back_to_the_global_ledger(self):
        # widened 2026-08-26 -- RICH_MANIFEST's own entries never have
        # username/hostname (the Named-Paths Manifest genuinely has no
        # such fields), only the global loads ledger does. host/
        # hostname consolidated into one function, "host", 2026-09-20 --
        # ip_address is retired (confirmed always-null in practice), so
        # this ledger fixture no longer carries it.
        ledger = [
            {
                "uuid": "v1-uuid",
                "username": "bot",
                "hostname": "worker-1",
            }
        ]
        assert (
            _finder(
                "$acme.csvpaths.:last():username()", RICH_MANIFEST, ledger=ledger
            )
            .resolve()
            .results[0]
            .data
            == "bot"
        )
        assert (
            _finder("$acme.csvpaths.:last():host()", RICH_MANIFEST, ledger=ledger)
            .resolve()
            .results[0]
            .data
            == "worker-1"
        )

    def test_username_no_matching_ledger_entry_gives_none(self):
        ledger = [{"uuid": "some-other-uuid", "username": "bot"}]
        results = _finder(
            "$acme.csvpaths.:last():username()", RICH_MANIFEST, ledger=ledger
        ).resolve()
        assert results.results[0].data is None


class TestResolveTargetLastWins:
    # added 2026-10-18 (compendium 5.20b), fixing a real, confirmed-live
    # bug: _extract_data()'s own field-accessor resolve-target site used
    # to pick the FIRST field accessor in the chain (via the shared
    # _find_field_function_call()), not the one a user chaining two of
    # them almost certainly means to read. "$acme.csvpaths.:last():
    # uuid():named_paths_name()" used to resolve to :uuid()'s own value
    # instead of :named_paths_name()'s.
    def test_last_of_two_chained_field_accessors_wins(self):
        manifest = [
            {**RICH_MANIFEST[0], "named_paths_name": "acme"},
            {**RICH_MANIFEST[1], "named_paths_name": "acme"},
        ]
        finder = _finder(
            "$acme.csvpaths.:last():uuid():named_paths_name()", manifest
        )
        results = finder.resolve()
        assert results.results[0].data == "acme"
        assert results.results[0].data != "v1-uuid"
        # 2 qualifying field accessors -> the ambiguity warning fires.
        assert len(finder.csvpaths.logger.warnings) == 1

    def test_reversed_order_still_picks_the_last_one(self):
        # proves this is genuinely about CHAIN POSITION, not just
        # ":named_paths_name()" always winning regardless of order --
        # users can choose the order to get the value they want
        # (David: "they know they can choose the correct order, if
        # there is a lack of clarity").
        manifest = [
            {**RICH_MANIFEST[0], "named_paths_name": "acme"},
            {**RICH_MANIFEST[1], "named_paths_name": "acme"},
        ]
        results = _finder(
            "$acme.csvpaths.:last():named_paths_name():uuid()", manifest
        ).resolve()
        assert results.results[0].data == "v1-uuid"

    def test_single_field_accessor_is_not_ambiguous_no_warning(self):
        finder = _finder("$acme.csvpaths.:last():uuid()", RICH_MANIFEST)
        finder.resolve()
        assert finder.csvpaths.logger.warnings == []


class TestNamedPathsHomeFunction:
    # :named_paths_home() -- added 2026-09-22, the CSVPATHS counterpart
    # to FILES' own :named_file_home(). SOURCE == "computed": never read
    # from a manifest entry (unlike :group_home(), which reads Table 3's
    # own stored "named_paths_home" field on an already-matched version
    # -- see test_group_home above), always derived directly from
    # root_major via paths_manager.named_paths_home(name).
    def test_bare_gives_every_versions_home_unreduced(self):
        results = _finder(
            "$acme.csvpaths.:named_paths_home()", RICH_MANIFEST
        ).resolve()
        assert [r.data for r in results.results] == [GROUP_HOME, GROUP_HOME]

    def test_combined_with_a_pointer_gives_the_one_matched_value(self):
        results = _finder(
            "$acme.csvpaths.:last():named_paths_home()", RICH_MANIFEST
        ).resolve()
        assert results.results[0].data == GROUP_HOME

    def test_star_traversal_reads_each_versions_group_home(self):
        # David, 2026-11-14 (decision W7, option B): a live version's home
        # is its group's. It raised "root_major must be a literal named-
        # paths group name" (RMF section 4, a spec-doc bug).
        by_name = {
            "alpha": [
                {
                    "group_file_path": "named_paths/alpha/group.csvpath",
                    "uuid": "a-v1",
                    "time": "2026-01-01T00:00:00+00:00",
                }
            ],
        }
        results = _finder("$*.csvpaths.:last():named_paths_home()", by_name=by_name).resolve()
        assert [r.data for r in results.results] == ["named_paths/alpha"]

    @pytest.mark.parametrize(
        "reference, expected",
        [
            # a ':manifest()' read gives each record's STORED
            # named_paths_home: the group manifest's for a live version
            # (6.13b(v); the key ':group_home()' reads), else the ledger's
            # -- also-v1's group entry has none, and gone-v1 (a deleted
            # group) and keep-reload (an unchanged reload) are ledger-only.
            # The stored values differ from the computed named_paths/<name>
            # to show which is read (reviewer on #618).
            (
                "$*.csvpaths.:manifest():named_paths_home()",
                ["S/keep", "L/also", "L/gone", "L/keep"],
            ),
            (
                '$:regex("^(keep|gone)$").csvpaths.:manifest():named_paths_home()',
                ["S/keep", "L/gone", "L/keep"],
            ),
            ("$*.csvpaths.:manifest():last():named_paths_home()", ["L/keep"]),
            # without ':manifest()', the literal reference for each live
            # group (6.13b(iv)): computed
            ("$*.csvpaths.:named_paths_home()", ["named_paths/keep", "named_paths/also"]),
            # ':all()' beside ':manifest()' stays a walk (ruling C Q1), so it
            # is the literal reference for each live group: computed, as
            # '$keep.csvpaths.:all():manifest():named_paths_home()' gives
            # (reviewer on #618; it read the stored homes)
            (
                "$*.csvpaths.:all():manifest():named_paths_home()",
                ["named_paths/also", "named_paths/keep"],
            ),
        ],
    )
    def test_a_traversal_root_reads_each_records_home(self, reference, expected):
        homes = {
            "keep-v1": "L/keep",
            "also-v1": "L/also",
            "gone-v1": "L/gone",
            "keep-reload": "L/keep",
        }
        ledger = [dict(e) for e in _C1_LEDGER]
        for e in ledger:
            e["named_paths_home"] = homes[e["uuid"]]
        finder = _finder(
            reference,
            by_name={
                "keep": [dict(_C1_KEEP, named_paths_home="S/keep")],
                "also": [dict(_C1_ALSO)],
            },
            ledger=ledger,
            inputs_csvpaths_path="named_paths",
        )
        assert [r.data for r in finder.resolve().results] == expected

def _one(results) -> object:
    """the data of the only result: a definition read is one result per
    group, never one per version (David, 2026-11-10)"""
    assert len(results.results) == 1
    return results.results[0].data


class TestDefinitionFieldAccessorFunctions:
    # :scripts()/:webhooks()/:transfers()/:destinations() are
    # SOURCE="definition" -- resolved against the named-paths group's
    # definition.json config, not a manifest entry. definition.json is
    # not versioned, so the group gives one result, and a version
    # selector beside the field raises (David, 2026-11-10: "there is no
    # such thing as a last destination"). These read through ':first()'
    # until then.
    DEFINITION = {
        "scripts": {"on_complete_all": "notify.sh"},
        "webhooks": {"on_complete_valid": {"url": "https://example.com/hook"}},
        "transfers": {
            "path_transfers": {
                "company_names": {
                    "on_complete_all": [{"file": "data", "transfer_to": "@out"}]
                }
            }
        },
        "destinations": {"main": {"address": "example.com", "port": 22}},
    }

    def test_scripts(self):
        results = _finder(
            "$acme.csvpaths.:scripts()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert _one(results) == {"on_complete_all": "notify.sh"}

    def test_webhooks(self):
        # headers defaults to [], not None, so exclude_none leaves it in
        # -- an empty list is not the same as an unset field.
        results = _finder(
            "$acme.csvpaths.:webhooks()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert _one(results) == {
            "on_complete_valid": {"url": "https://example.com/hook", "headers": []}
        }

    def test_transfers_reads_the_nested_path_transfers_key(self):
        results = _finder(
            "$acme.csvpaths.:transfers()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert _one(results) == {
            "company_names": {
                "on_complete_all": [{"file": "data", "transfer_to": "@out"}]
            }
        }

    def test_destinations(self):
        results = _finder(
            "$acme.csvpaths.:destinations()", RICH_MANIFEST, self.DEFINITION
        ).resolve()
        assert _one(results) == {"main": {"address": "example.com", "port": 22}}

    def test_never_configured_gives_none_not_an_error(self):
        results = _finder(
            "$acme.csvpaths.:scripts()", RICH_MANIFEST
        ).resolve()
        assert _one(results) is None

    @pytest.mark.parametrize(
        "reference",
        [
            "$acme.csvpaths.:first():scripts()",
            "$acme.csvpaths.:scripts():last()",
            "$acme.csvpaths.:index(0):scripts()",
            "$acme.csvpaths.:all():scripts()",
            "$acme.csvpaths.:from(0):to(1):scripts()",
            "$acme.csvpaths.:manifest():scripts()",
            '$acme.csvpaths.:having("company_names"):scripts()',
            '$acme.csvpaths.:last():destination_address("main")',
            "$*.csvpaths.:last():scripts()",
            "$*.csvpaths.:all():scripts()",
            "$*.csvpaths.:manifest():scripts()",
        ],
    )
    def test_a_version_selector_beside_it_raises(self, reference):
        with pytest.raises(ReferenceException3) as error:
            _finder(reference, RICH_MANIFEST, self.DEFINITION).query()
        message = str(error.value)
        assert "definition.json, which is not versioned" in message
        assert "Use it alone in name_one" in message


class TestDefinitionSubFieldAccessorFunctions:
    # the arg-keyed (destinations.<name>.*, transfers.<name>.
    # on_complete_*) and fixed-state (scripts.on_complete_*, webhooks.
    # on_complete_*) sub-field accessors built 2026-08-26 -- see
    # ReferenceFinder3._apply_key_arg()'s own docstring for the shared
    # "{}"-placeholder mechanism the arg-keyed ones need.
    DEFINITION = {
        "scripts": {
            "on_complete_all": "notify.sh",
            "on_complete_error": "alert.sh",
        },
        "webhooks": {
            "on_complete_valid": {"url": "https://example.com/hook"},
        },
        "transfers": {
            "path_transfers": {
                "company_names": {
                    "on_complete_all": [{"file": "data", "transfer_to": "@out"}]
                }
            }
        },
        "destinations": {
            "main": {
                "address": "example.com",
                "port": 22,
                "username": "bot",
                "password": "secret",
            }
        },
    }

    def test_script_on_complete_all(self):
        results = _finder(
            "$acme.csvpaths.:script_on_complete_all()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == "notify.sh"

    def test_script_on_complete_error(self):
        results = _finder(
            "$acme.csvpaths.:script_on_complete_error()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == "alert.sh"

    def test_script_on_complete_valid_not_configured_gives_none(self):
        results = _finder(
            "$acme.csvpaths.:script_on_complete_valid()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) is None

    def test_webhooks_on_complete_valid(self):
        results = _finder(
            "$acme.csvpaths.:webhooks_on_complete_valid()",
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == {
            "url": "https://example.com/hook",
            "headers": [],
        }

    def test_destination_address_by_name(self):
        results = _finder(
            '$acme.csvpaths.:destination_address("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == "example.com"

    def test_destination_port_by_name(self):
        results = _finder(
            '$acme.csvpaths.:destination_port("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == 22

    def test_destination_username_by_name(self):
        results = _finder(
            '$acme.csvpaths.:destination_username("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == "bot"

    def test_destination_password_by_name(self):
        results = _finder(
            '$acme.csvpaths.:destination_password("main")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == "secret"

    def test_destination_unknown_name_gives_none_not_an_error(self):
        results = _finder(
            '$acme.csvpaths.:destination_address("nope")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) is None

    def test_transfer_on_complete_all_by_identity(self):
        results = _finder(
            '$acme.csvpaths.:transfer_on_complete_all("company_names")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == [
            {"file": "data", "transfer_to": "@out"}
        ]

    def test_transfer_on_complete_unknown_identity_gives_none(self):
        results = _finder(
            '$acme.csvpaths.:transfer_on_complete_all("nope")',
            RICH_MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) is None


class TestTemplateBareVsPointerDualSource:
    # :template() (built 2026-08-26) is the first field accessor using
    # Function3.BARE_SOURCE -- bare (the whole of name_one) reads
    # definition.json's current default; with anything that selects
    # versions beside it, it reads each matched version's own manifest
    # snapshot instead. Until 2026-11-08 only a pointer counted, so a
    # range, ':all()' or ':manifest()' gave the current default for every
    # version (David: "we need to return the versions' templates").
    # Bare is a definition read, one result for the group (2026-11-10).
    # See Template3's own docstring for the full design.
    MANIFEST = [
        {**RICH_MANIFEST[0], "template": "snapshot-v0"},
        {**RICH_MANIFEST[1], "template": "snapshot-v1"},
    ]
    DEFINITION = {"template": "current-default"}

    def test_bare_reads_the_current_definition_default(self):
        results = _finder(
            "$acme.csvpaths.:template()", self.MANIFEST, self.DEFINITION
        ).resolve()
        # one result: definition.json is not versioned. Was one per
        # version, each the same current default.
        assert _one(results) == "current-default"

    def test_definition_beside_it_reads_the_same_default(self):
        # a regression in #565 read each version's snapshot here
        results = _finder(
            "$acme.csvpaths.:definition():template()",
            self.MANIFEST,
            self.DEFINITION,
        ).resolve()
        assert _one(results) == "current-default"

    @pytest.mark.parametrize(
        "reference",
        [
            "$acme.csvpaths.:definition():last():template()",
            "$acme.csvpaths.:definition():all():template()",
            "$acme.csvpaths.:definition():from(0):to(1):template()",
        ],
    )
    def test_definition_with_a_version_selector_raises(self, reference):
        # one source or a set of sources, not both (David, 2026-11-10)
        with pytest.raises(ReferenceException3) as error:
            _finder(reference, self.MANIFEST, self.DEFINITION).query()
        assert "definition.json is not versioned" in str(error.value)

    def test_first_reads_that_versions_own_manifest_snapshot(self):
        results = _finder(
            "$acme.csvpaths.:first():template()", self.MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == "snapshot-v0"

    def test_last_reads_that_versions_own_manifest_snapshot(self):
        results = _finder(
            "$acme.csvpaths.:last():template()", self.MANIFEST, self.DEFINITION
        ).resolve()
        assert results.results[0].data == "snapshot-v1"

    def test_bare_never_configured_gives_none_not_an_error(self):
        results = _finder(
            "$acme.csvpaths.:template()", self.MANIFEST
        ).resolve()
        assert _one(results) is None

    @pytest.mark.parametrize(
        "reference, expected",
        [
            ("$acme.csvpaths.:all():template()", ["snapshot-v0", "snapshot-v1"]),
            (
                "$acme.csvpaths.:from(0):to(1):template()",
                ["snapshot-v0", "snapshot-v1"],
            ),
            ("$acme.csvpaths.:from(-1):template()", ["snapshot-v1"]),
            ("$acme.csvpaths.:manifest():template()", ["snapshot-v0", "snapshot-v1"]),
            (
                "$acme.csvpaths.:manifest():from(1):template()",
                ["snapshot-v1"],
            ),
        ],
    )
    def test_selecting_versions_reads_each_versions_own_snapshot(
        self, reference, expected
    ):
        results = _finder(reference, self.MANIFEST, self.DEFINITION).resolve()
        assert [r.data for r in results.results] == expected

    def test_the_ledger_reads_each_versions_own_snapshot(self):
        # every load in the root ledger, a deleted group's (g1) included
        results = _gate_finder("$*.csvpaths.:manifest():template()").resolve()
        assert [(r.uuid, r.data) for r in results.results] == [
            ("a1", ""),
            ("b1", ""),
            ("a2", ":1/:2"),
            ("g1", ":y"),
            ("a3", ":1"),
            ("b2", ":x"),
            ("a4", ""),
        ]


#
# a definition read (David, 2026-11-10): definition.json is one record per
# named-paths group, not versioned, so ':definition()' with fields, or a
# bare definition field, gives one result per group -- the FILES E3 rules
# (TestDefinitionChain there), shared in ReferenceFinder3.
#
DEF_BY_NAME = {
    "acme": {
        "template": ":1/:2",
        "destinations": {"myd": {"address": "ftp.acme.example"}},
        "scripts": {"on_complete_all": "acme.sh"},
    },
    "beta": {"scripts": {"on_complete_all": "beta.sh"}},
}


def _def_chain_finder(reference: str) -> CsvpathsReferenceFinder3:
    return _finder(
        reference,
        by_name={name: [dict(e) for e in es] for name, es in GATE_BY_NAME.items()},
        ledger=[dict(e) for e in GATE_LEDGER],
        definitions_by_name=DEF_BY_NAME,
        inputs_csvpaths_path="named_paths",
    )


def _def_chain_values(reference: str) -> list:
    return [r.data for r in _def_chain_finder(reference).resolve().results]


class TestDefinitionChain:
    @pytest.mark.parametrize(
        "reference",
        [
            '$acme.csvpaths.:destination_address("myd")',
            '$acme.csvpaths.:definition():destination_address("myd")',
            '$acme.csvpaths.:destination_address("myd"):definition()',
        ],
    )
    def test_a_field_value_is_one_result(self, reference):
        assert _def_chain_values(reference) == ["ftp.acme.example"]

    def test_the_query_path_is_the_definition_file(self):
        results = _def_chain_finder("$acme.csvpaths.:definition():scripts()").query()
        assert results.files == [pathu.resep("named_paths/acme/definition.json")]
        assert results.uuids == [None]
        assert not results.ambiguous_content_read

    @pytest.mark.parametrize(
        "root, expected",
        [
            ("$*", ["acme.sh", "beta.sh"]),
            ('$:regex("^b")', ["beta.sh"]),
            ('$:choice("acme|beta")', ["acme.sh", "beta.sh"]),
        ],
    )
    def test_each_live_group_under_a_traversal_root(self, root, expected):
        # one per live group: the deleted g1 has no definition.json
        values = _def_chain_values(f"{root}.csvpaths.:scripts()")
        assert [v["on_complete_all"] for v in values] == expected

    @pytest.mark.parametrize(
        "reference",
        [
            "$*.csvpaths.:definition(:template(:has_value()))",
            "$*.csvpaths.:definition():template(:has_value())",
            "$*.csvpaths.:template(:has_value())",
        ],
    )
    def test_a_predicate_filters_nested_or_chained(self, reference):
        results = _def_chain_finder(reference).query()
        assert results.files == [pathu.resep("named_paths/acme/definition.json")]

    def test_a_filter_with_a_value(self):
        reference = "$*.csvpaths.:definition():template(:has_value()):scripts()"
        assert _def_chain_values(reference) == [{"on_complete_all": "acme.sh"}]

    def test_two_filters_are_anded(self):
        base = "$*.csvpaths.:definition():template(:has_value())"
        both = _def_chain_finder(f"{base}:template(:has_value())").query()
        assert both.files == [pathu.resep("named_paths/acme/definition.json")]
        none = _def_chain_finder(f"{base}:template(:does_not_have_value())")
        assert none.query().results == []

    def test_the_last_value_field_wins_with_a_warning(self):
        finder = _def_chain_finder("$acme.csvpaths.:definition():scripts():template()")
        assert [r.data for r in finder.resolve().results] == [":1/:2"]
        assert len(finder.csvpaths.logger.warnings) == 1

    def test_with_no_value_field_resolves_the_file(self):
        # a filter only: the whole definition.json, one group, so it
        # resolves (compendium 6.19)
        results = _def_chain_finder(
            '$:regex("^a").csvpaths.:definition(:template(:has_value()))'
        ).query()
        assert results.files == [pathu.resep("named_paths/acme/definition.json")]
        assert not results.ambiguous_content_read

    @pytest.mark.parametrize("field", ["uuid()", "time()", "named_paths_name()"])
    def test_a_field_not_in_definition_json_raises(self, field):
        with pytest.raises(ReferenceException3) as error:
            _def_chain_finder(f"$acme.csvpaths.:definition():{field}").query()
        message = str(error.value)
        assert "does not read a named-paths group's definition.json" in message

    @pytest.mark.parametrize(
        "function", ["last()", "index(1)", "all()", "from(1)", "manifest()"]
    )
    def test_a_version_selector_in_the_chain_raises(self, function):
        with pytest.raises(ReferenceException3) as error:
            _def_chain_finder(f"$acme.csvpaths.:definition():{function}").query()
        assert "definition.json is not versioned" in str(error.value)

    def test_name_three_raises(self):
        with pytest.raises(ReferenceException3) as error:
            _def_chain_finder("$acme.csvpaths.:scripts().company_names").query()
        assert "':definition()' chain with name_three" in str(error.value)

    def test_a_bare_star_definition_with_name_three_raises(self):
        with pytest.raises(ReferenceException3) as error:
            _def_chain_finder("$*.csvpaths.:definition().company_names").query()
        assert "definition.json is not versioned" in str(error.value)

    def test_the_template_beside_a_selector_is_still_a_version_read(self):
        # ':template()' is in the version records too: beside a selector
        # it reads each version's own (#565), not the definition
        assert _def_chain_values("$acme.csvpaths.:all():template()") == [
            "",
            ":1/:2",
            ":1",
            "",
        ]


class TestScopeLimits:
    def test_star_root_major_now_supported(self):
        # not-yet-supported sweep #9, 2026-10-20 -- this was a real
        # scope limit (name_three unconditionally rejected during '*'
        # traversal), now lifted; see TestStarTraversalFlatten's own
        # test_name_three_now_composes_with_traversal for the full
        # positive-match coverage. With the DEFAULT fixture here (no
        # by_name -- named_paths_names comes back empty, see
        # _FakePathsManager's own docstring), '*' traversal matches no
        # groups at all, so this now resolves to empty results rather
        # than raising -- confirms query() itself no longer blocks this
        # shape outright.
        finder = _finder("$*.csvpaths.:last().x")
        results = finder.query()
        assert results.results == []

    def test_name_two_worksheet_marker_not_yet_supported(self):
        finder = _finder("$acme.csvpaths.:last()#sheet1.x")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_literal_path_in_name_one_not_supported(self):
        finder = _finder("$acme.csvpaths.somefile.x")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_star_in_name_one_not_supported(self):
        finder = _finder("$acme.csvpaths.*.x")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_two_pointers_in_name_one_raises(self):
        finder = _finder("$acme.csvpaths.:first():last()")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_function_chain_on_name_three_not_yet_supported(self):
        finder = _finder("$acme.csvpaths.:last().company_names:data()")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_star_body_on_name_three_not_supported(self):
        finder = _finder("$acme.csvpaths.:last().*")
        with pytest.raises(ReferenceException3):
            finder.query()

    def test_metadata_kind_unreachable_via_a_real_reference(self):
        # :meta() is a real registered function (Meta3, RESOLVES_AS ==
        # Reference3.METADATA_FILE -- see Function3.metadata_kind()),
        # but query() would already reject this reference for a
        # different reason first (functions on name_three are rejected
        # outright for csvpaths), so _extract_data() is called directly
        # to test its own resolve_kind branching in isolation -- this
        # confirms the generic resolve_kind fallback (not-yet-supported
        # sweep #10) is a defensive safety net, not a pending gap.
        finder = _finder("$acme.csvpaths.:first().:meta()")
        with pytest.raises(ReferenceException3):
            finder._extract_data(ReferenceResult3(path="p", uuid="v0-uuid"))


class TestPositionEnforcement:
    # ReferenceFinder3._check_position() -- added 2026-08-14, the
    # enforced replacement for the scattered "is this recognized"
    # guards each Finder used to hand-write on its own. CSVPATHS is the
    # first Finder retrofitted to call it.
    def test_name_is_registered_for_csvpaths_but_has_nowhere_legal_to_go(self):
        # the actual bug this mechanism was built to close: :name()'s
        # own DATATYPES includes csvpaths (it type-checks fine as an
        # argument-typed function), but it has no path-building
        # dimension there -- POSITIONS[csvpaths] is an explicit empty
        # tuple, not an absent key, so this now raises instead of
        # silently no-opping the way it used to.
        with pytest.raises(ReferenceException3):
            _finder('$acme.csvpaths.:name("x")').query()

    def test_a_function_not_declared_for_csvpaths_at_all_is_rejected(self):
        # :mark() is FILES-only in its own DATATYPES and has no
        # POSITIONS entry for csvpaths at all -- same rejection path,
        # different starting point (never declared vs. declared-empty).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:first():mark()", RICH_MANIFEST).query()

    def test_a_legal_function_is_unaffected(self):
        # sanity check that the new check does not over-reject --
        # :having() legitimately declares name_one for csvpaths.
        results = _finder(
            '$acme.csvpaths.:having("company_names"):last()', RICH_MANIFEST
        ).query()
        assert results.uuids == ["v0-uuid"]

    def test_having_is_not_legal_at_name_three(self):
        # :having() only declares name_one -- riding on name_three
        # (where it has never been meaningful) is rejected the same way.
        with pytest.raises(ReferenceException3):
            _finder('$acme.csvpaths.:last().:having("x")', RICH_MANIFEST).query()


class TestLog:
    # compendium 5.16(b) -- an outlier: a single, global, datatype-
    # independent resource (config.ini's own log_file), not tied to any
    # named-paths group at all. Built and shared identically across all
    # three finders (ReferenceFinder3._bare_log_call()/_query_log_call()/
    # _read_log_file()) -- this class exercises the full scenario set
    # once here (csvpaths needs no real fixture beyond a log file path,
    # simplest of the three datatypes to set up); see
    # test_files_reference_finder_3.py/test_results_reference_finder_3.py
    # for one confirming end-to-end test each, proving the shared
    # mechanism composes correctly with each datatype's own query()
    # dispatch too, not just in isolation.
    def test_bare_log_resolves_the_whole_file(self, tmp_path):
        log_path = tmp_path / "csvpath.log"
        log_path.write_text("line1\nline2\nline3\n")
        results = _finder("$*.csvpaths.:log()", log_file=str(log_path)).resolve()
        assert results.results[0].data == "line1\nline2\nline3\n"

    def test_log_with_int_arg_gives_last_n_lines(self, tmp_path):
        log_path = tmp_path / "csvpath.log"
        log_path.write_text("\n".join(f"line{i}" for i in range(1, 21)) + "\n")
        results = _finder("$*.csvpaths.:log(3)", log_file=str(log_path)).resolve()
        assert results.results[0].data == "line18\nline19\nline20"

    def test_log_resolves_none_when_file_does_not_exist_yet(self, tmp_path):
        log_path = tmp_path / "does-not-exist.log"
        results = _finder("$*.csvpaths.:log()", log_file=str(log_path)).resolve()
        assert results.results[0].data is None

    def test_log_combined_with_a_pointer_is_rejected(self):
        # "standalone, not-combinable" -- riding alongside anything else
        # in name_one is illegal, even a plain pointer.
        with pytest.raises(ReferenceException3):
            _finder("$*.csvpaths.:log():last()", log_file="x.log").query()

    def test_log_with_literal_root_major_is_rejected(self):
        # root_major must be '*' -- a literal named-paths group name is
        # misleading here (there is no acme-specific log content).
        with pytest.raises(ReferenceException3):
            _finder("$acme.csvpaths.:log()", log_file="x.log").query()


REGEX_BY_NAME = {
    "acme_group": [
        {
            "group_file_path": "named_paths/acme_group/group.csvpath",
            "uuid": "acme-v1",
            "time": "2026-01-01T00:00:00+00:00",
            "named_paths_identities": [],
        }
    ],
    "abba_group": [
        {
            "group_file_path": "named_paths/abba_group/group.csvpath",
            "uuid": "abba-v1",
            "time": "2026-01-02T00:00:00+00:00",
            "named_paths_identities": [],
        }
    ],
}


class TestRegexRootMajor:
    # :regex() at root_major -- added 2026-08-27, the crowded-namespace
    # motivating case (David): "acme_group"/"abba_group" are more
    # manageable when a reference can target "/abba_.*/" directly.
    # Reuses CsvpathsReferenceFinder3's own '*'-traversal machinery,
    # just pre-filtered by pattern before it enumerates
    # named_paths_names.
    def test_regex_filters_to_matching_groups(self):
        results = _finder(
            "$:regex(/^abba_.*/).csvpaths.:last()", by_name=REGEX_BY_NAME
        ).query()
        assert results.uuids == ["abba-v1"]

    def test_regex_excludes_non_matching_groups(self):
        results = _finder(
            "$:regex(/^abba_.*/).csvpaths.:last()", by_name=REGEX_BY_NAME
        ).query()
        assert "acme-v1" not in results.uuids

    def test_regex_with_no_matches_gives_empty(self):
        results = _finder(
            "$:regex(/^zzz_.*/).csvpaths.:last()", by_name=REGEX_BY_NAME
        ).query()
        assert results.uuids == []

    def test_wrong_root_major_function_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                '$:having("x").csvpaths.:last()', by_name=REGEX_BY_NAME
            ).query()

    def test_regex_accepts_a_registered_variable(self):
        results = _finder(
            "$:regex(@aregex).csvpaths.:last()",
            by_name=REGEX_BY_NAME,
            variables={"aregex": "^abba_.*"},
        ).query()
        assert results.uuids == ["abba-v1"]

    def test_content_resolution_finds_the_correct_group(self):
        # proves _group_manifest_entry()'s own widened multi-group
        # search (see TestGroupManifestEntry above) composes correctly
        # through a real query()+resolve() -- not just unit-tested in
        # isolation.
        results = _finder(
            "$:regex(/^abba_.*/).csvpaths.:last():uuid()",
            by_name=REGEX_BY_NAME,
        ).resolve()
        assert results.results[0].data == "abba-v1"


class TestChoiceRootMajor:
    # :choice() at root_major -- added 2026-10-20, the exact-match
    # sibling of :regex() just above. Minimal symmetric coverage --
    # the real behavioral tests live in test_files_reference_finder_3.py
    # (TestChoiceRootMajor/TestChoiceAsNameOnePathSegment); this just
    # confirms CsvpathsReferenceFinder3 wires it the same way.
    def test_choice_filters_to_listed_groups(self):
        results = _finder(
            '$:choice("abba_group|zzz_nonexistent").csvpaths.:last()',
            by_name=REGEX_BY_NAME,
        ).query()
        assert results.uuids == ["abba-v1"]

    def test_choice_does_not_partial_match(self):
        results = _finder(
            '$:choice("abba").csvpaths.:last()', by_name=REGEX_BY_NAME
        ).query()
        assert results.uuids == []


#
# a root ledger with a deleted group ("gone": no per-name manifest, no
# definition) and an unchanged reload of keep (its own uuid, linked to
# the version it matched by version_uuid). the ledger spells some keys
# differently from a per-name entry, and its own "manifest_path" is the
# ledger itself, so reading the wrong source shows.
#
_C1_LEDGER_PATH = "named_paths/manifest.json"
_C1_KEEP = {
    "named_paths_name": "keep",
    "group_file_path": "named_paths/keep/group.csvpaths",
    "uuid": "keep-v1",
    "fingerprint": "fp-keep",
    "time": "2026-01-01T00:00:00+00:00",
    "named_paths_identities": ["s"],
    "manifest_path": "named_paths/keep/manifest.json",
}
_C1_ALSO = {
    "named_paths_name": "also",
    "group_file_path": "named_paths/also/group.csvpaths",
    "uuid": "also-v1",
    "fingerprint": "fp-also",
    "time": "2026-01-02T00:00:00+00:00",
    "named_paths_identities": ["t"],
    "manifest_path": "named_paths/also/manifest.json",
}


def _c1_ledger_entry(
    *, name: str, uuid: str, fingerprint: str, time: str, lifecycle: str, **extra
) -> dict:
    entry = {
        "named_paths_name": name,
        "group_file_path": f"named_paths/{name}/group.csvpaths",
        "uuid": uuid,
        "fingerprint": fingerprint,
        "time": time,
        "hostname": f"host-{name}",
        "status": "complete",
        "lifecycle": lifecycle,
        "paths_manifest": f"named_paths/{name}/manifest.json",
        "manifest_path": _C1_LEDGER_PATH,
    }
    entry.update(extra)
    return entry


_C1_LEDGER = [
    _c1_ledger_entry(
        name="keep",
        uuid="keep-v1",
        fingerprint="fp-keep",
        time="2026-01-01T00:00:00+00:00",
        lifecycle="active",
    ),
    _c1_ledger_entry(
        name="also",
        uuid="also-v1",
        fingerprint="fp-also",
        time="2026-01-02T00:00:00+00:00",
        lifecycle="active",
    ),
    _c1_ledger_entry(
        name="gone",
        uuid="gone-v1",
        fingerprint="fp-gone",
        time="2026-01-03T00:00:00+00:00",
        lifecycle="deleted",
    ),
    _c1_ledger_entry(
        name="keep",
        uuid="keep-reload",
        fingerprint="fp-keep",
        time="2026-01-04T00:00:00+00:00",
        lifecycle="active",
        status="unchanged",
        version_uuid="keep-v1",
    ),
]
_C1_LEDGER_UUIDS = ["keep-v1", "also-v1", "gone-v1", "keep-reload"]


class TestStarLedgerReadKeepsDeletedEntries:
    # finding C1 of the :lifecycle() gate work (specs/references_v3/
    # notes/v3_part_2_lifecycle_gate.md), added 2026-10-30. Under '*', a
    # ':manifest()' chain, or a field with no pointer, reads the root
    # ledger, deleted entries included (David: "a ledger read returns the
    # whole ledger"; the compendium's bare and ':manifest()' forms both
    # "search the ledger manifest"). Entries are first-class. A live
    # version reads its per-name entry first; a deleted one, or an
    # unchanged reload, has only its ledger entry. A bare pointer
    # without ':manifest()', and ':all()', still walk the live groups.
    @staticmethod
    def _c1_finder(reference: str) -> CsvpathsReferenceFinder3:
        return _finder(
            reference,
            by_name={"keep": [dict(_C1_KEEP)], "also": [dict(_C1_ALSO)]},
            ledger=[dict(e) for e in _C1_LEDGER],
            definitions_by_name={
                "keep": {"scripts": {"on_complete_all": "keep.py"}},
                "also": {"scripts": {"on_complete_all": "also.py"}},
            },
            inputs_csvpaths_path="named_paths",
        )

    def _data(self, reference: str) -> list:
        return [r.data for r in self._c1_finder(reference).resolve().results]

    def test_bare_field_lists_the_live_versions_only(self):
        # changed 2026-11-01 (C1 bare-half revert, agreed with David; was:
        # every ledger entry). A bare '*' field reads each live group in
        # turn, sorted by time; only ':manifest()' reaches the ledger, so
        # the deleted gone-v1 and the unchanged reload keep-reload drop out.
        results = self._c1_finder("$*.csvpaths.:uuid()").query()
        assert results.uuids == ["keep-v1", "also-v1"]
        assert results.files == [
            "named_paths/keep/group.csvpaths",
            "named_paths/also/group.csvpaths",
        ]

    def test_manifest_field_lists_every_ledger_entry(self):
        results = self._c1_finder("$*.csvpaths.:manifest():uuid()").query()
        assert results.uuids == _C1_LEDGER_UUIDS

    @pytest.mark.parametrize(
        "root", ["$*", '$:regex("^(keep|gone)$")', '$:choice("keep|gone")']
    )
    @pytest.mark.parametrize(
        "tail, expected",
        [
            # keep-v1, gone-v1, keep-reload under the filtered roots
            (".csvpaths.:manifest():last()", "keep-reload"),
            (".csvpaths.:last():manifest()", "keep-reload"),
            (".csvpaths.:manifest():first()", "keep-v1"),
        ],
    )
    def test_a_ledger_record_resolves_under_every_traversal_root(
        self, root, tail, expected
    ):
        # a ledger-only record (the unchanged reload keep-reload, the
        # deleted gone-v1) resolves to its ledger entry under ':regex()'
        # and ':choice()' as under '*' (6.13b, 6.13b(i), C1). It resolved
        # to None there until 2026-11-12: the ledger fallback was Star3
        # only.
        assert [e["uuid"] for e in self._data(root + tail)] == [expected]

    @pytest.mark.parametrize(
        "root", ['$:regex("^(keep|gone)$")', '$:choice("keep|gone")']
    )
    def test_a_deleted_record_resolves_under_a_filtered_root(self, root):
        # gone-v1 is index 1 of the name-filtered set
        data = self._data(root + ".csvpaths.:manifest():index(1)")
        assert [e["uuid"] for e in data] == ["gone-v1"]

    def test_deleted_entry_path_is_the_ledger(self):
        # changed 2026-11-01 (was: its group file). Every record of the
        # '*' manifest set gives the ledger's path (compendium 5.7).
        results = self._c1_finder("$*.csvpaths.:manifest():uuid()").query()
        assert results.results[2].uuid == "gone-v1"
        assert results.results[2].path == "named_paths/manifest.json"

    def test_bare_field_values_are_the_live_versions(self):
        # changed 2026-11-01 (was: include the deleted entry)
        assert self._data("$*.csvpaths.:uuid()") == ["keep-v1", "also-v1"]
        assert self._data("$*.csvpaths.:fingerprint()") == ["fp-keep", "fp-also"]

    def test_manifest_last_with_a_field_is_the_last_ledger_entry(self):
        assert self._data("$*.csvpaths.:manifest():last():uuid()") == ["keep-reload"]

    def test_a_field_does_not_change_which_entry_last_picks(self):
        plain = self._c1_finder("$*.csvpaths.:manifest():last()").query()
        with_field = self._c1_finder("$*.csvpaths.:manifest():last():uuid()").query()
        assert plain.uuids == with_field.uuids

    def test_manifest_index_picks_the_deleted_entry(self):
        assert self._data("$*.csvpaths.:manifest():index(2):uuid()") == ["gone-v1"]

    def test_manifest_first_is_unchanged(self):
        assert self._data("$*.csvpaths.:manifest():first():uuid()") == ["keep-v1"]

    def test_deleted_entry_values_come_from_its_ledger_entry(self):
        assert self._data("$*.csvpaths.:manifest():index(2):fingerprint()") == [
            "fp-gone"
        ]
        assert self._data("$*.csvpaths.:manifest():index(2):time()") == [
            "2026-01-03T00:00:00+00:00"
        ]
        assert self._data("$*.csvpaths.:manifest():index(2):named_paths_name()") == [
            "gone"
        ]

    def test_per_version_data_is_none_for_the_deleted_entry(self):
        assert self._data("$*.csvpaths.:manifest():named_paths_identities()") == [
            ["s"],
            ["t"],
            None,
            None,
        ]

    def test_a_definition_field_on_the_ledger_raises(self):
        # the ledger is a set of versions, and definition.json has none
        # (2026-11-10). Gave each entry's group definition, None for the
        # deleted group's.
        with pytest.raises(ReferenceException3) as error:
            self._data("$*.csvpaths.:manifest():scripts()")
        assert "definition.json, which is not versioned" in str(error.value)

    def test_having_drops_the_deleted_entry(self):
        results = self._c1_finder('$*.csvpaths.:manifest():having("s"):uuid()').query()
        assert results.uuids == ["keep-v1"]

    def test_manifest_path_is_the_per_name_manifest_for_every_entry(self):
        assert self._data("$*.csvpaths.:manifest():manifest_path()") == [
            "named_paths/keep/manifest.json",
            "named_paths/also/manifest.json",
            "named_paths/gone/manifest.json",
            "named_paths/keep/manifest.json",
        ]

    def test_ledger_only_field_for_every_entry(self):
        assert self._data("$*.csvpaths.:manifest():host()") == [
            "host-keep",
            "host-also",
            "host-gone",
            "host-keep",
        ]

    def test_unchanged_reload_is_its_own_entry(self):
        results = self._c1_finder("$*.csvpaths.:manifest():uuid()").query()
        assert results.uuids.count("keep-reload") == 1
        assert results.uuids.count("keep-v1") == 1

    def test_regex_root_filters_the_ledger(self):
        results = self._c1_finder(
            '$:regex("^(keep|gone)$").csvpaths.:manifest():uuid()'
        ).query()
        assert results.uuids == ["keep-v1", "gone-v1", "keep-reload"]

    def test_bare_pointer_still_reads_the_live_groups(self):
        # one result per live group (compendium 4.1b)
        assert sorted(self._data("$*.csvpaths.:last():uuid()")) == [
            "also-v1",
            "keep-v1",
        ]

    def test_grouped_shape_still_reads_the_live_groups(self):
        results = self._c1_finder("$*.csvpaths.:all():uuid()").query()
        assert sorted(results.uuids) == ["also-v1", "keep-v1"]

    def test_ledger_entry_rejects_none(self):
        with pytest.raises(ValueError):
            self._c1_finder("$*.csvpaths.:uuid()")._ledger_entry(None)

    def test_ledger_entry_of_an_unknown_uuid_is_none(self):
        assert self._c1_finder("$*.csvpaths.:uuid()")._ledger_entry("nope") is None


ACME_MANIFEST_JSON = "named_paths/acme/manifest.json"
C1_LEDGER_MANIFEST_JSON = "named_paths/manifest.json"


class TestManifestEntryQueryPaths:
    # added 2026-11-01. A reference with an explicit ':manifest()' names
    # a manifest entry, a record, so query() gives the manifest.json the
    # entry is read from, with the entry's uuid (compendium 5.7; agreed
    # with David 2026-11-01): the group's own manifest, or the root
    # ledger for the '*' manifest set (C1). These used to give the
    # group file. Forms without ':manifest()' keep the group file.

    @pytest.mark.parametrize(
        "reference,uuids",
        [
            ("$acme.csvpaths.:last():manifest()", ["v1-uuid"]),
            ("$acme.csvpaths.:manifest():last()", ["v1-uuid"]),
            ("$acme.csvpaths.:first():manifest()", ["v0-uuid"]),
            ("$acme.csvpaths.:all():manifest()", ["v0-uuid", "v1-uuid"]),
            ("$acme.csvpaths.:manifest():uuid()", ["v0-uuid", "v1-uuid"]),
            ("$acme.csvpaths.:last():manifest():uuid()", ["v1-uuid"]),
        ],
    )
    def test_literal_root_gives_the_groups_manifest(self, reference, uuids):
        results = _finder(reference).query()
        assert results.uuids == uuids
        assert results.files == [ACME_MANIFEST_JSON] * len(uuids)

    @pytest.mark.parametrize(
        "reference", ["$acme.csvpaths.:last()", "$acme.csvpaths.:last():uuid()"]
    )
    def test_without_manifest_the_version_keeps_the_group_file(self, reference):
        assert _finder(reference).query().files == [GROUP_FILE_PATH]

    def test_bare_manifest_is_still_the_whole_file(self):
        results = _finder("$acme.csvpaths.:manifest()").query()
        assert results.files == [ACME_MANIFEST_JSON]
        assert results.uuids == [None]

    def test_literal_resolve_still_gives_the_entry(self):
        results = _finder("$acme.csvpaths.:last():manifest()").resolve()
        assert results.results[0].data == ACME_MANIFEST[1]

    def test_star_group_gives_each_groups_own_manifest(self):
        results = _star_finder("$*.csvpaths.:all():last():manifest()").query()
        assert [(r.path, r.uuid) for r in results.results] == [
            ("named_paths/alpha/manifest.json", "a-v2"),
            ("named_paths/beta/manifest.json", "b-v1"),
        ]

    def test_star_group_without_a_pointer_lists_every_entry(self):
        results = _star_finder("$*.csvpaths.:all():manifest()").query()
        assert [(r.path, r.uuid) for r in results.results] == [
            ("named_paths/alpha/manifest.json", "a-v1"),
            ("named_paths/alpha/manifest.json", "a-v2"),
            ("named_paths/beta/manifest.json", "b-v1"),
        ]

    def test_star_group_resolve_reads_each_groups_entry(self):
        results = _star_finder("$*.csvpaths.:all():last():manifest()").resolve()
        assert [r.data for r in results.results] == [
            STAR_ALPHA_MANIFEST[1],
            STAR_BETA_MANIFEST[0],
        ]

    def test_star_without_manifest_keeps_the_group_file(self):
        results = _star_finder("$*.csvpaths.:all():last()").query()
        assert results.files == [
            "named_paths/alpha/group.csvpath",
            "named_paths/beta/group.csvpath",
        ]

    @staticmethod
    def _c1(reference: str):
        return TestStarLedgerReadKeepsDeletedEntries._c1_finder(reference)

    @pytest.mark.parametrize(
        "reference,uuids",
        [
            ("$*.csvpaths.:manifest():uuid()", _C1_LEDGER_UUIDS),
            ("$*.csvpaths.:manifest():last():uuid()", ["keep-reload"]),
            ('$*.csvpaths.:manifest():having("s"):uuid()', ["keep-v1"]),
            ('$*.csvpaths.:manifest():having("s")', ["keep-v1"]),
            ("$*.csvpaths.:manifest():first()", ["keep-v1"]),
            ("$*.csvpaths.:manifest():last()", ["keep-reload"]),
        ],
    )
    def test_the_star_manifest_set_gives_the_ledger(self, reference, uuids):
        results = self._c1(reference).query()
        assert results.uuids == uuids
        assert results.files == [C1_LEDGER_MANIFEST_JSON] * len(uuids)

    def test_a_bare_star_field_keeps_the_group_files(self):
        # no ':manifest()': Group 3, unchanged here (the C1 bare-half
        # revert will move it off the ledger).
        results = self._c1("$*.csvpaths.:uuid()").query()
        assert C1_LEDGER_MANIFEST_JSON not in results.files

    def test_a_live_set_record_resolves_to_its_groups_entry(self):
        # R2, fixed 2026-11-01: the pointer form read the ledger entry
        # though keep-v1 is live. named_paths_identities is only in the
        # group's own entry.
        for reference in [
            "$*.csvpaths.:manifest():first()",
            '$*.csvpaths.:manifest():having("s")',
        ]:
            data = self._c1(reference).resolve().results[0].data
            assert data == _C1_KEEP, reference

    def test_a_deleted_set_record_resolves_to_its_ledger_entry(self):
        data = self._c1("$*.csvpaths.:manifest():index(2)").resolve().results[0].data
        assert data == _C1_LEDGER[2]

    def test_an_unchanged_reload_resolves_to_its_ledger_entry(self):
        data = self._c1("$*.csvpaths.:manifest():last()").resolve().results[0].data
        assert data == _C1_LEDGER[3]


class TestVersionResultPath:
    # the helper behind TestManifestEntryQueryPaths.

    @staticmethod
    def _finder():
        return _finder("$acme.csvpaths.:last()", inputs_csvpaths_path="named_paths")

    def test_each_source(self):
        finder = self._finder()
        version = ACME_MANIFEST[0]
        assert finder._version_result_path(version=version, manifest_source=None) == (
            GROUP_FILE_PATH
        )
        assert finder._version_result_path(
            version=version, manifest_source=finder.GROUP_MANIFEST
        ) == ACME_MANIFEST_JSON
        assert finder._version_result_path(
            version=version, manifest_source=finder.LEDGER_MANIFEST
        ) == C1_LEDGER_MANIFEST_JSON

    def test_bad_arguments_raise(self):
        finder = self._finder()
        with pytest.raises(TypeError):
            finder._version_result_path(version=None, manifest_source=None)
        with pytest.raises(ValueError):
            finder._version_result_path(version={"uuid": "u"}, manifest_source=None)
        with pytest.raises(ValueError):
            finder._version_result_path(
                version=ACME_MANIFEST[0], manifest_source="elsewhere"
            )
        # checked up front, even with no versions to give a path to
        with pytest.raises(ValueError):
            finder._apply_name_three_to_versions([], None, manifest_source="elsewhere")


class TestBareStarFieldReadsLiveGroups:
    # C1 bare-half revert (2026-11-01, agreed with David; compendium 6.19):
    # a bare '*' field with no pointer reads each live group in turn,
    # sorted by time. Only ':manifest()' reaches the ledger set.
    @staticmethod
    def _c1(reference: str):
        return TestStarLedgerReadKeepsDeletedEntries._c1_finder(reference)

    @pytest.mark.parametrize(
        "reference",
        [
            "$*.csvpaths.:uuid()",
            '$:regex("^(keep|also|gone)$").csvpaths.:uuid()',
            '$:choice("keep|also|gone").csvpaths.:uuid()',
        ],
    )
    def test_live_groups_only(self, reference):
        assert self._c1(reference).query().uuids == ["keep-v1", "also-v1"]

    def test_a_name_filter_still_narrows(self):
        results = self._c1('$:regex("^keep$").csvpaths.:uuid()').query()
        assert results.uuids == ["keep-v1"]

    def test_the_manifest_set_still_reads_the_ledger(self):
        results = self._c1("$*.csvpaths.:manifest():uuid()").query()
        assert results.uuids == _C1_LEDGER_UUIDS

    def test_a_bare_field_resolves_from_the_live_entry(self):
        data = [
            r.data
            for r in self._c1("$*.csvpaths.:named_paths_identities()").resolve().results
        ]
        assert data == [["s"], ["t"]]

    def test_a_pointer_reads_the_live_groups_one_per_group(self):
        # a bare pointer under '*' walks the live groups, one result per
        # group (finding I, compendium 4.1b)
        assert sorted(self._c1("$*.csvpaths.:last()").query().uuids) == [
            "also-v1",
            "keep-v1",
        ]


class TestArguedUuidFilters:
    # an argued ':uuid()' beside a pointer is a filter, then the pointer
    # picks, as in RESULTS (David, 2026-11-06; compendium 6.44). The
    # finding A fixture: acme a1-a4, beta b1-b2, gone's g1 deleted.
    @pytest.mark.parametrize(
        "reference, expected",
        [
            ('$acme.csvpaths.:last():uuid("a1")', ["a1"]),
            ('$acme.csvpaths.:uuid("a1"):last()', ["a1"]),
            ('$acme.csvpaths.:last():uuid("b1")', []),
            ('$*.csvpaths.:last():uuid("a1")', ["a1"]),
            ('$*.csvpaths.:uuid("b1"):first()', ["b1"]),
            ('$*.csvpaths.:uuid("a1")', ["a1"]),
            ('$*.csvpaths.:all():uuid("b2")', ["b2"]),
            ('$*.csvpaths.:manifest():uuid("g1")', ["g1"]),
            ('$*.csvpaths.:manifest():last():uuid("g1")', ["g1"]),
            # with another gate, ANDed in either order
            ('$acme.csvpaths.:last():uuid("a1"):lifecycle("active")', ["a1"]),
            ('$*.csvpaths.:manifest():lifecycle("active"):uuid("g1")', []),
            ('$*.csvpaths.:manifest():uuid("g1"):lifecycle("deleted")', ["g1"]),
        ],
    )
    def test_a_filter_then_the_pointer(self, reference, expected):
        assert _gate_finder(reference).query().uuids == expected

    def test_the_bare_lookup_is_unchanged(self):
        assert _gate_finder('$acme.csvpaths.:uuid("a2")').query().uuids == ["a2"]


class TestComparisonOnAMissingValue:
    # W3, option A (David, 2026-11-14): a missing value is neither above
    # nor below a bound; the record does not match, and the skip is
    # logged, naming the field and the record. Both shapes raised
    # TypeError.
    def test_a_version_gate_skips_a_version_with_no_template(self):
        # a copy of the gate fixture where a1 has no template at all; a4's
        # is "" (present, and not above "")
        by_name = {name: [dict(e) for e in es] for name, es in GATE_BY_NAME.items()}
        for entry in by_name["acme"]:
            if entry["uuid"] == "a1":
                del entry["template"]
        finder = _finder(
            '$acme.csvpaths.:all():template(:above(""))',
            by_name=by_name,
            ledger=[dict(e) for e in GATE_LEDGER],
            inputs_csvpaths_path="named_paths",
        )
        assert finder.query().uuids == ["a2", "a3"]
        warnings = finder.csvpaths.logger.warnings
        assert len(warnings) == 1
        assert "a1" in warnings[0] and ":template()" in warnings[0]
        assert ":above()" in warnings[0]

    def test_a_definition_field_comparison_skips_a_group_without_it(self):
        # acme's definition.json has no on_arrival
        finder = _gate_finder('$acme.csvpaths.:on_arrival(:above("a"))')
        assert finder.query().results == []
        warnings = finder.csvpaths.logger.warnings
        assert len(warnings) == 1
        assert "acme" in warnings[0] and ":on_arrival()" in warnings[0]
