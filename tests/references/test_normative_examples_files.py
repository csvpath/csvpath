"""Encodes the currently-buildable FILES examples from
`references_notes/notes/normative_reference_examples.txt` as real, running
assertions -- same methodology as `test_normative_examples_results.py`:
David's own agreed alternative to relying on manual code review against the
doc, rely on the normative references instead.

Scope: FILES only. Every example in the doc's "The Files Datatype" section
was verified against real code on 2026-08-11 (per the section's own note),
and all of it is built -- there is nothing to exclude here the way RESULTS
had unbuilt time/filter functions to skip. Doc lines are given by their
current position in the doc as of 2026-08-12; each test is commented with
the exact line(s) it encodes. When the doc's FILES section changes, update
the line references here to match.
"""

import json

import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3


class _FakeFileDescriber:
    def __init__(self, definition: dict):
        self._definition = definition

    def get_config(self, name):
        from csvpath.managers.files.file_descriptor import Config

        return Config(**self._definition)


class _FakeFileManager:
    def __init__(
        self,
        home,
        manifest,
        definition: dict | None = None,
        ledger=None,
        by_name: dict | None = None,
    ):
        self._home = home
        self._manifest = manifest
        self._definition = definition or {}
        self._ledger = manifest if ledger is None else ledger
        self._by_name = by_name

    def named_file_home(self, name):
        if self._by_name is not None:
            return self._by_name[name][0]
        return self._home

    def get_manifest(self, name):
        if self._by_name is not None:
            return self._by_name[name][1]
        return self._manifest

    @property
    def named_file_names(self):
        if self._by_name is not None:
            return list(self._by_name.keys())
        return []

    @property
    def files_root_manifest(self):
        return self._ledger

    @property
    def describer(self):
        return _FakeFileDescriber(self._definition)


class _FakeConfig:
    def __init__(self, inputs_files_path: str | None = None):
        self.inputs_files_path = inputs_files_path


class _FakeCsvPaths:
    def __init__(self, file_manager, inputs_files_path: str | None = None):
        self.file_manager = file_manager
        self.config = _FakeConfig(inputs_files_path)


def _finder(
    reference: str,
    home: str,
    manifest: list,
    definition: dict | None = None,
    inputs_files_path: str | None = None,
    ledger: list | None = None,
    by_name: dict | None = None,
) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakeFileManager(home, manifest, definition, ledger=ledger, by_name=by_name),
        inputs_files_path=inputs_files_path,
    )
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return FilesReferenceFinder3(csvpaths=csvpaths, ref=ref)


ALPHA_HOME = "inputs/named_files/alpha"
ALPHA_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/orders.csv/aaa.csv",
        "file_home": "inputs/named_files/alpha/orders.csv",
        "uuid": "u-orders-1",
    },
    {
        "file": "inputs/named_files/alpha/orders.csv/bbb.csv",
        "file_home": "inputs/named_files/alpha/orders.csv",
        "uuid": "u-orders-2",
    },
    {
        "file": "inputs/named_files/alpha/returns.csv/ccc.csv",
        "file_home": "inputs/named_files/alpha/returns.csv",
        "uuid": "u-returns-1",
    },
    {
        "file": "inputs/named_files/alpha/orders.csv/ddd.csv",
        "file_home": "inputs/named_files/alpha/orders.csv",
        "uuid": "u-orders-3",
    },
]


class TestLiteralNamedFileOneVersion:
    # doc lines "### Literal named-file, one version" -- the pointer/
    # accessor lives in name_three, chained after a "." onto :name(...).
    def test_last(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:last()', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert results.uuids == ["u-orders-3"]

    def test_first(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:first()', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert results.uuids == ["u-orders-1"]

    def test_index_is_zero_based(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:index(1)', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert results.uuids == ["u-orders-2"]


class TestEveryVersionUnreduced:
    # doc line "### Every version of a literal named-file, unreduced"
    def test_every_version_of_one_named_path(self):
        results = _finder(
            '$alpha.files.:name("orders.csv")', ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert results.uuids == [None]
        assert results.files == ["inputs/named_files/alpha/orders.csv"]


class TestPoolAcrossOneNamedFileExactlyOneLevel:
    # doc line "$alpha.files.*.:last()" -- pools every EXACTLY-one-level
    # path under alpha (orders.csv AND returns.csv) into one list, in
    # true manifest-array arrival order (the last entry written wins,
    # not the last alphabetically) -- confirms cross-path pooling, not
    # just within one already-known path.
    def test_last_across_every_one_level_path(self):
        results = _finder("$alpha.files.*.:last()", ALPHA_HOME, ALPHA_MANIFEST).query()
        assert results.uuids == ["u-orders-3"]

    def test_first_across_every_one_level_path(self):
        results = _finder("$alpha.files.*.:first()", ALPHA_HOME, ALPHA_MANIFEST).query()
        assert results.uuids == ["u-orders-1"]


MIXED_HOME = "inputs/named_files/mixed"
MIXED_MANIFEST = [
    {
        "file": "inputs/named_files/mixed/zero.csv/aaa.csv",
        "file_home": "inputs/named_files/mixed/zero.csv",
        "uuid": "u-zero-1",
    },
    {
        "file": "inputs/named_files/mixed/zero.csv/bbb.csv",
        "file_home": "inputs/named_files/mixed/zero.csv",
        "uuid": "u-zero-2",
    },
    {
        "file": "inputs/named_files/mixed/nested/deep.csv/ccc.csv",
        "file_home": "inputs/named_files/mixed/nested/deep.csv",
        "uuid": "u-deep-1",
    },
    {
        "file": "inputs/named_files/mixed/nested/deep.csv/ddd.csv",
        "file_home": "inputs/named_files/mixed/nested/deep.csv",
        "uuid": "u-deep-2",
    },
]


class TestAllForOneNamedFile:
    # doc lines "### ':all()' for ONE named-file" -- every distinct path
    # under one named-file, EXACTLY one level deep (same match as '*'),
    # each independently reduced -- corrected 2026-08-12 to stay a
    # one-level peer of '*', matching RESULTS' own vocabulary. Uses
    # ALPHA_MANIFEST (orders.csv x3, returns.csv x1, both one level).
    def test_all_last_gives_each_paths_own_latest(self):
        results = _finder(
            "$alpha.files.:all().:last()", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert set(results.uuids) == {"u-orders-3", "u-returns-1"}

    def test_all_first_gives_each_paths_own_earliest(self):
        results = _finder(
            "$alpha.files.:all().:first()", ALPHA_HOME, ALPHA_MANIFEST
        ).query()
        assert set(results.uuids) == {"u-orders-1", "u-returns-1"}

    def test_all_alone_gives_every_distinct_one_level_path_unreduced(self):
        results = _finder("$alpha.files.:all()", ALPHA_HOME, ALPHA_MANIFEST).query()
        assert set(results.files) == {
            "inputs/named_files/alpha/orders.csv",
            "inputs/named_files/alpha/returns.csv",
        }


class TestFlattenForOneNamedFile:
    # doc lines "### ':flatten()' for ONE named-file" -- the any-depth
    # POOL peer of ':all()' (one-level GROUP)/'*' (one-level POOL),
    # added 2026-08-12. MIXED_MANIFEST has two distinct file_homes at
    # DIFFERENT depths -- exactly what '*'/':all()' cannot reach.
    def test_flatten_last_pools_across_every_depth(self):
        results = _finder(
            "$mixed.files.:flatten().:last()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert results.uuids == ["u-deep-2"]

    def test_flatten_first_pools_across_every_depth(self):
        results = _finder(
            "$mixed.files.:flatten().:first()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert results.uuids == ["u-zero-1"]

    def test_flatten_alone_gives_every_distinct_path_any_depth_unreduced(self):
        results = _finder("$mixed.files.:flatten()", MIXED_HOME, MIXED_MANIFEST).query()
        assert set(results.files) == {
            "inputs/named_files/mixed/zero.csv",
            "inputs/named_files/mixed/nested/deep.csv",
        }


class TestGroupsForOneNamedFile:
    # doc lines "### ':groups()' for ONE named-file" -- the any-depth
    # GROUP peer of ':all()' (one-level GROUP)/':flatten()' (any-depth
    # POOL), added 2026-08-12. Reaches both of MIXED_MANIFEST's distinct
    # depths, each independently reduced -- the mixed-depth case ':all()'
    # cannot reach on its own.
    def test_groups_last_gives_each_paths_own_latest_at_any_depth(self):
        results = _finder(
            "$mixed.files.:groups().:last()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert set(results.uuids) == {"u-zero-2", "u-deep-2"}

    def test_groups_first_gives_each_paths_own_earliest_at_any_depth(self):
        results = _finder(
            "$mixed.files.:groups().:first()", MIXED_HOME, MIXED_MANIFEST
        ).query()
        assert set(results.uuids) == {"u-zero-1", "u-deep-1"}

    def test_groups_alone_gives_every_distinct_path_any_depth_unreduced(self):
        results = _finder("$mixed.files.:groups()", MIXED_HOME, MIXED_MANIFEST).query()
        assert set(results.files) == {
            "inputs/named_files/mixed/zero.csv",
            "inputs/named_files/mixed/nested/deep.csv",
        }


class TestManifestEitherOrder:
    # doc lines "### The version's own manifest entry, either order"
    def test_pointer_then_manifest(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:last():manifest()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[3]

    def test_manifest_then_pointer(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:manifest():last()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).resolve()
        assert results.results[0].data == ALPHA_MANIFEST[3]


class TestDefinitionBare:
    # doc line "$alpha.files.:definition()" -- bare, no :name(.../version
    # needed, since definition.json is per named-file not per-version.
    def test_resolves_the_raw_definition_bytes(self, tmp_path):
        content = b'{"sources": {}}'
        home = tmp_path / "alpha"
        home.mkdir()
        (home / "definition.json").write_bytes(content)
        results = _finder(
            "$alpha.files.:definition()", str(home), ALPHA_MANIFEST
        ).resolve()
        assert results.results[0].data == content


RICH_HOME = "inputs/named_files/rich"
RICH_MANIFEST = [
    {
        "file": "inputs/named_files/rich/orders.csv/aaaa.csv",
        "file_home": "inputs/named_files/rich/orders.csv",
        "uuid": "u-rich-1",
        "time": "2026-01-01T00:00:00+00:00",
        "fingerprint": "aaaa",
        "from": "/staging/orders.csv",
        "mark": "Sheet1",
    },
    {
        "file": "inputs/named_files/rich/orders.csv/bbbb.csv",
        "file_home": "inputs/named_files/rich/orders.csv",
        "uuid": "u-rich-2",
        "time": "2026-02-01T00:00:00+00:00",
        "fingerprint": "bbbb",
        "from": "/staging/orders.csv",
    },
]
RICH_DEFINITION = {
    "on_arrival": {
        "named_paths_group": "order validations",
        "run_method": "collect_paths",
    },
    "sources": {"a": {"address": "localhost", "port": 22}},
}


class TestDefinitionFieldAccessorsNeedAMatchedVersion:
    # doc lines "### on_arrival/sources sub-objects DO need a matched
    # version + '.' + accessor, even though the value is the same
    # regardless of which version matched" -- SOURCE="definition", not
    # versioned, but still syntactically hangs off a matched version.
    def test_on_arrival(self):
        results = _finder(
            '$rich.files.:name("orders.csv").:first():on_arrival()',
            RICH_HOME,
            RICH_MANIFEST,
            RICH_DEFINITION,
        ).resolve()
        assert results.results[0].data == RICH_DEFINITION["on_arrival"]

    def test_sources(self):
        results = _finder(
            '$rich.files.:name("orders.csv").:first():sources()',
            RICH_HOME,
            RICH_MANIFEST,
            RICH_DEFINITION,
        ).resolve()
        assert results.results[0].data == RICH_DEFINITION["sources"]


class TestGlobalArrivalsLedger:
    # doc line "### Global arrivals ledger -- every named-file's own
    # arrival, one flat array"
    def test_resolves_the_ledgers_raw_bytes(self, tmp_path):
        content = b'[{"named_file_name": "alpha"}, {"named_file_name": "beta"}]'
        root = tmp_path / "named_files"
        root.mkdir()
        (root / "manifest.json").write_bytes(content)
        results = _finder(
            "$*.files.:manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path=str(root),
        ).resolve()
        assert results.results[0].data == content


LEDGER = [
    {"named_file_name": "alpha", "uuid": "u-ledger-1"},
    {"named_file_name": "beta", "uuid": "u-ledger-2"},
    {"named_file_name": "gamma", "uuid": "u-ledger-3"},
]


class TestGlobalArrivalsLedgerOrdinalIndexing:
    # doc lines "### Ordinal indexing into the global ledger, either order"
    def test_pointer_then_manifest(self):
        results = _finder(
            "$*.files.:last():manifest()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        ).resolve()
        assert results.results[0].data == LEDGER[-1]

    def test_manifest_then_pointer(self):
        results = _finder(
            "$*.files.:manifest():last()",
            ALPHA_HOME,
            ALPHA_MANIFEST,
            inputs_files_path="inputs/named_files",
            ledger=LEDGER,
        ).query()
        assert results.results[0].uuid == "u-ledger-3"


#
# matches the spec compendium's own EXAMPLE SCENARIO ("Why a trailing bare
# '*' is illegal but bare ':all()' is fine"): named-file alpha (zero.csv x1
# version, one.csv x2 versions), named-file beta (two.csv x2 versions).
# beta listed FIRST on purpose -- naive concatenation with no time-sort
# would put alpha's own entries last, so a test asserting beta's true-
# latest entry wins fails if the pool case's time-sort is ever broken.
#
STAR_ALPHA_HOME = "inputs/named_files/alpha"
STAR_ALPHA_MANIFEST = [
    {
        "file": "inputs/named_files/alpha/zero.csv/aaa.csv",
        "file_home": "inputs/named_files/alpha/zero.csv",
        "uuid": "u-zero-1",
        "time": "2026-01-01T00:00:00+00:00",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/bbb.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-1",
        "time": "2026-01-02T00:00:00+00:00",
    },
    {
        "file": "inputs/named_files/alpha/one.csv/ccc.csv",
        "file_home": "inputs/named_files/alpha/one.csv",
        "uuid": "u-one-2",
        "time": "2026-01-03T00:00:00+00:00",
    },
]
STAR_BETA_HOME = "inputs/named_files/beta"
STAR_BETA_MANIFEST = [
    {
        "file": "inputs/named_files/beta/two.csv/ddd.csv",
        "file_home": "inputs/named_files/beta/two.csv",
        "uuid": "u-two-1",
        "time": "2026-01-04T00:00:00+00:00",
    },
    {
        "file": "inputs/named_files/beta/two.csv/eee.csv",
        "file_home": "inputs/named_files/beta/two.csv",
        "uuid": "u-two-2",
        "time": "2026-01-05T00:00:00+00:00",
    },
]
STAR_BY_NAME = {
    "beta": (STAR_BETA_HOME, STAR_BETA_MANIFEST),
    "alpha": (STAR_ALPHA_HOME, STAR_ALPHA_MANIFEST),
}


def _star_finder(reference: str) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakeFileManager(None, None, by_name=STAR_BY_NAME),
    )
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return FilesReferenceFinder3(csvpaths=csvpaths, ref=ref)


class TestStarTraversalPool:
    # doc line "### '*' traversal, POOL -- single true-latest version
    # across every named-file, each match still exactly one level deep"
    def test_last_across_every_named_file(self):
        results = _star_finder("$*.files.*.:last()").query()
        assert results.uuids == ["u-two-2"]


class TestStarTraversalGroup:
    # doc line "### '*' traversal, GROUP -- one result per (named-file,
    # path) pair, each match still exactly one level deep"
    def test_all_last_gives_one_result_per_named_file_and_path(self):
        results = _star_finder("$*.files.:all().:last()").query()
        assert set(results.uuids) == {"u-zero-1", "u-one-2", "u-two-2"}


FLATTEN_GAMMA_HOME = "inputs/named_files/gamma"
FLATTEN_GAMMA_MANIFEST = [
    {
        "file": "inputs/named_files/gamma/nested/deep.csv/fff.csv",
        "file_home": "inputs/named_files/gamma/nested/deep.csv",
        "uuid": "u-gamma-deep-1",
        "time": "2026-01-06T00:00:00+00:00",
    },
]
FLATTEN_BY_NAME = dict(STAR_BY_NAME, gamma=(FLATTEN_GAMMA_HOME, FLATTEN_GAMMA_MANIFEST))


def _flatten_star_finder(reference: str) -> FilesReferenceFinder3:
    csvpaths = _FakeCsvPaths(_FakeFileManager(None, None, by_name=FLATTEN_BY_NAME))
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return FilesReferenceFinder3(csvpaths=csvpaths, ref=ref)


class TestStarTraversalFlattenAnyDepth:
    # doc line "### '*' traversal, POOL, any depth" -- gamma's two-level
    # entry (chronologically latest) is reachable only by ':flatten()',
    # not by '*' (exactly one level).
    def test_last_reaches_a_two_level_entry_star_cannot(self):
        star_results = _flatten_star_finder("$*.files.*.:last()").query()
        assert star_results.uuids == ["u-two-2"]
        flatten_results = _flatten_star_finder("$*.files.:flatten().:last()").query()
        assert flatten_results.uuids == ["u-gamma-deep-1"]


class TestStarTraversalGroupsAnyDepth:
    # doc line "### '*' traversal, GROUP, any depth" -- one result per
    # (named-file, path) pair regardless of depth, including gamma's
    # two-level entry that ':all()' cannot reach.
    def test_last_gives_one_result_per_named_file_and_path_any_depth(self):
        groups_results = _flatten_star_finder("$*.files.:groups().:last()").query()
        assert set(groups_results.uuids) == {
            "u-zero-1",
            "u-one-2",
            "u-two-2",
            "u-gamma-deep-1",
        }


class TestFieldAccessorsOnOneMatchedVersion:
    # doc lines "### Field accessors on one matched version"
    def test_uuid(self):
        results = _finder(
            '$rich.files.:name("orders.csv").:last():uuid()',
            RICH_HOME,
            RICH_MANIFEST,
        ).resolve()
        assert results.results[0].data == "u-rich-2"

    def test_time(self):
        results = _finder(
            '$rich.files.:name("orders.csv").:last():time()',
            RICH_HOME,
            RICH_MANIFEST,
        ).resolve()
        assert results.results[0].data == "2026-02-01T00:00:00+00:00"

    def test_fingerprint(self):
        results = _finder(
            '$rich.files.:name("orders.csv").:last():fingerprint()',
            RICH_HOME,
            RICH_MANIFEST,
        ).resolve()
        assert results.results[0].data == "bbbb"

    def test_home_gives_file_home(self):
        results = _finder(
            '$rich.files.:name("orders.csv").:last():home()',
            RICH_HOME,
            RICH_MANIFEST,
        ).resolve()
        assert results.results[0].data == "inputs/named_files/rich/orders.csv"

    def test_origin(self):
        results = _finder(
            '$rich.files.:name("orders.csv").:last():origin()',
            RICH_HOME,
            RICH_MANIFEST,
        ).resolve()
        assert results.results[0].data == "/staging/orders.csv"

    def test_mark_absent_gives_none(self):
        # RICH_MANIFEST[1] (the last/most recent version) has no "mark"
        # key -- absence is a normal, expected None, not an error.
        results = _finder(
            '$rich.files.:name("orders.csv").:last():mark()',
            RICH_HOME,
            RICH_MANIFEST,
        ).resolve()
        assert results.results[0].data is None


class TestPathFunction:
    # doc lines "### The filesystem path to a whole-resource function's
    # own resource, rather than its content"
    def test_path_wrapping_manifest_bare(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:path(:manifest())',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).resolve()
        assert results.results[0].data == f"{ALPHA_HOME}/manifest.json"

    def test_path_wrapping_manifest_beside_a_pointer(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:last():path(:manifest())',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).resolve()
        assert results.results[0].data == f"{ALPHA_HOME}/manifest.json"


class TestComputedFields:
    # doc lines "### Computed fields -- never stored, derived from the
    # reference itself"
    def test_named_file_name(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:named_file_name()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).resolve()
        assert [r.data for r in results.results] == ["alpha", "alpha", "alpha"]

    def test_named_file_home(self):
        results = _finder(
            '$alpha.files.:name("orders.csv").:first():named_file_home()',
            ALPHA_HOME,
            ALPHA_MANIFEST,
        ).resolve()
        assert results.results[0].data == ALPHA_HOME
