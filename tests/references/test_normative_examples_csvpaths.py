"""Encodes the currently-buildable CSVPATHS examples from
`references_notes/notes/normative_reference_examples.txt` as real, running
assertions -- same methodology as `test_normative_examples_results.py`/
`test_normative_examples_files.py`: David's own agreed alternative to relying
on manual code review against the doc, rely on the normative references
instead.

Scope: CSVPATHS only. Every example in the doc's "The Csvpaths Datatype"
section was re-verified against real code on 2026-08-13 (live-tested via
ad-hoc scripts before writing these, not just re-run from memory), and all of
it is built -- there is nothing to exclude. The one aspirational QUESTION
line in the doc (cross-group, identity-filtered '*' traversal) is
deliberately NOT encoded here -- it is explicitly marked "not buildable yet"
in the doc itself, so a test for it would just be locking in a
ReferenceException3, not confirming a real capability; see
TestScopeLimits.test_star_traversal_combined_with_name_three_is_not_yet_supported
in test_csvpaths_reference_finder_3.py for that raise, already covered there.

Doc lines are given by their current heading text as of 2026-08-13; when the
doc's CSVPATHS section changes, update the references here to match.
"""

import pytest

from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_parser_3 import ReferenceParser3


class _FakePathsDescriber:
    def __init__(self, definition: dict):
        self._definition = definition

    def get_config(self, name):
        from csvpath.managers.paths.paths_descriptor import GroupConfig

        return GroupConfig(**self._definition)


class _FakePathsManager:
    def __init__(
        self,
        manifest,
        home: str,
        definition: dict | None = None,
        ledger=None,
        by_name: dict | None = None,
    ):
        self._manifest = manifest
        self._home = home
        self._definition = definition or {}
        self._ledger = manifest if ledger is None else ledger
        # by_name: {name: manifest} -- only used by '*' traversal/global
        # ledger tests, which need more than one distinct named-paths group.
        self._by_name = by_name

    def get_manifest_for_name(self, name):
        if self._by_name is not None:
            return self._by_name[name]
        return self._manifest

    def named_paths_home(self, name):
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
        return _FakePathsDescriber(self._definition)


class _FakeConfig:
    def __init__(self, inputs_csvpaths_path: str | None = None):
        self.inputs_csvpaths_path = inputs_csvpaths_path


class _FakeCsvPaths:
    def __init__(self, paths_manager, inputs_csvpaths_path: str | None = None):
        self.paths_manager = paths_manager
        self.config = _FakeConfig(inputs_csvpaths_path)


def _finder(
    reference: str,
    manifest: list,
    home: str = "named_paths/acme",
    definition: dict | None = None,
    inputs_csvpaths_path: str | None = None,
    ledger: list | None = None,
    by_name: dict | None = None,
) -> CsvpathsReferenceFinder3:
    csvpaths = _FakeCsvPaths(
        _FakePathsManager(
            manifest, home=home, definition=definition, ledger=ledger, by_name=by_name
        ),
        inputs_csvpaths_path=inputs_csvpaths_path,
    )
    ref = ReferenceParser3(string=reference, csvpaths=csvpaths)
    return CsvpathsReferenceFinder3(csvpaths=csvpaths, ref=ref)


#
# "acme" -- the doc's own running single-group example throughout its
# Csvpaths section. v0 (earliest) is the only version carrying the
# "my_validations" identity -- deliberately NOT also on v1 (the latest), so
# ':having()'/':all()' + name_three examples give a genuinely different
# answer than a bare pointer would, rather than a coincidentally identical
# one. v1 (latest) carries both a named ("company_names") and an unnamed
# (stringified load-time index "0") statement, for the identity-lookup
# section's own two literal doc examples.
#
GROUP_FILE_PATH = "named_paths/acme/group.csvpath"
GROUP_HOME = "named_paths/acme"
ACME_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v0-uuid",
        "named_paths": ["stmt my_validations text"],
        "named_paths_identities": ["my_validations"],
    },
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v1-uuid",
        "named_paths": ["stmt anonymous text", "stmt company_names text"],
        "named_paths_identities": ["0", "company_names"],
    },
]


class TestVersionPointerAndEveryVersionUnreduced:
    # doc lines "### Version pointer / every version unreduced"
    def test_last(self):
        results = _finder("$acme.csvpaths.:last()", ACME_MANIFEST).query()
        assert results.uuids == ["v1-uuid"]

    def test_first(self):
        results = _finder("$acme.csvpaths.:first()", ACME_MANIFEST).query()
        assert results.uuids == ["v0-uuid"]

    def test_index(self):
        results = _finder("$acme.csvpaths.:index(1)", ACME_MANIFEST).query()
        assert results.uuids == ["v1-uuid"]

    def test_bare_all_gives_every_version_unreduced(self):
        results = _finder("$acme.csvpaths.:all()", ACME_MANIFEST).query()
        assert results.uuids == ["v0-uuid", "v1-uuid"]


class TestAllFilteredByNameThree:
    # doc lines "### the set of my_validations csvpath statements from every
    # version of the acme group" -- FIXED wording 2026-08-12: root_major is
    # the literal group `acme`, not '*'.
    def test_all_dot_identity_gives_only_versions_containing_it(self):
        results = _finder("$acme.csvpaths.:all().my_validations", ACME_MANIFEST).query()
        assert results.uuids == ["v0-uuid"]


class TestAllIsRedundantBesideARealPointer:
    # doc lines "### NOT YET BUILT AS WRITTEN" -- confirmed via direct
    # testing: once a real pointer (:last()) is present, ':all()' is
    # silently ignored (redundant, pointer wins -- same rule as FILES' own
    # ':all()' in name_three), so "$acme.csvpaths.:all():last().my_validations"
    # reduces to just "acme's own last version, if it has a my_validations
    # statement" -- here it does NOT (only v0 has it, and :last() is v1), so
    # this gives EMPTY, not "the last version of every group that has one."
    def test_all_beside_last_reduces_to_just_the_last_version_filtered(self):
        results = _finder(
            "$acme.csvpaths.:all():last().my_validations", ACME_MANIFEST
        ).query()
        assert results.uuids == []

    def test_identical_to_the_same_query_with_all_omitted(self):
        # proves ':all()' contributed nothing once a real pointer is present.
        with_all = _finder(
            "$acme.csvpaths.:all():last().company_names", ACME_MANIFEST
        ).query()
        without_all = _finder("$acme.csvpaths.:last().company_names", ACME_MANIFEST).query()
        assert with_all.uuids == without_all.uuids == ["v1-uuid"]

    # the doc's own QUESTION line ("$*.csvpaths.:all():last().my_validations"
    # -- the cross-group, identity-filtered form this NOT-YET-BUILT note
    # actually wanted) is deliberately not encoded here -- see module
    # docstring.


class TestHaving:
    # doc lines "### ':having(\"identity\")'" and "### ':having()' alone" --
    # filters the version list down to versions whose own
    # named_paths_identities actually contains that identity, BEFORE any
    # pointer reduces further. Only v0 has "my_validations", so ':having()'
    # gives a genuinely different answer than a bare ':last()' would.
    def test_having_then_pointer_reduces_the_filtered_list(self):
        results = _finder(
            '$acme.csvpaths.:having("my_validations"):last()', ACME_MANIFEST
        ).query()
        assert results.uuids == ["v0-uuid"]

    def test_having_alone_lists_every_matching_version_unreduced(self):
        # confirmed 2026-08-13 to be already built, correcting an earlier
        # doc draft that mismarked this "NOT YET BUILT".
        results = _finder(
            '$acme.csvpaths.:having("my_validations")', ACME_MANIFEST
        ).query()
        assert results.uuids == ["v0-uuid"]


#
# a 5-version "acme" for the name_one VERSION range section -- each version
# carries its own "time" (registration/load time) and identities, one of
# which ("my_validations") only appears on the earliest version, mirroring
# the same having-then-range composition the doc's own last example needs.
#
VERSION_RANGE_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": f"v{i}-uuid",
        "named_paths": [f"stmt {i} text"],
        "named_paths_identities": ["my_validations"] if i == 0 else [str(i)],
        "time": f"2026-01-0{i + 1}T00:00:00+00:00",
    }
    for i in range(5)
]


class TestVersionRange:
    # doc lines "### ':from()'/':to()' as a name_one VERSION range" --
    # windows the (possibly ':having()'-filtered) version list; a real
    # pointer riding alongside reduces the RANGE, not the full candidate
    # set. Two modes: index-mode POSITIONALLY slices, date-mode FILTERS by
    # each version's own "time" manifest field.
    def test_from_index_negative_gives_the_last_n_versions(self):
        results = _finder("$acme.csvpaths.:from(-3)", VERSION_RANGE_MANIFEST).query()
        assert results.uuids == ["v2-uuid", "v3-uuid", "v4-uuid"]

    def test_from_and_to_together_with_a_pointer_reduces_the_range(self):
        results = _finder(
            "$acme.csvpaths.:from(1):to(3):last()", VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v3-uuid"]

    def test_date_mode_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            '$acme.csvpaths.:from(:date("2026-01-01")):to(:date("2026-01-31"))',
            VERSION_RANGE_MANIFEST,
        ).query()
        assert results.uuids == [f"v{i}-uuid" for i in range(5)]

    def test_having_filters_before_the_range_windows(self):
        results = _finder(
            '$acme.csvpaths.:having("my_validations"):from(-3)', VERSION_RANGE_MANIFEST
        ).query()
        assert results.uuids == ["v0-uuid"]


#
# "acme" with its last version carrying 5 statements -- the name_three
# STATEMENT range section needs at least 4 (for the doc's own
# ":from(1):to(3)" inclusive example).
#
STATEMENT_RANGE_MANIFEST = [
    ACME_MANIFEST[0],
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v1-uuid",
        "named_paths": [f"stmt {i} text" for i in range(5)],
        "named_paths_identities": [str(i) for i in range(5)],
    },
]


class TestStatementRange:
    # doc lines "### ':from()'/':to()' as a name_three STATEMENT range" --
    # David's own FlightPath v2 use case: rewind/replay starting from a
    # specific csvpath statement.
    def test_from_index_windows_the_matched_versions_own_statement_list(self):
        results = _finder(
            "$acme.csvpaths.:last().:from(:index(2))", STATEMENT_RANGE_MANIFEST
        ).query()
        assert [r.identity for r in results.results] == ["2", "3", "4"]
        assert results.uuids == ["v1-uuid", "v1-uuid", "v1-uuid"]

    def test_from_and_to_together_is_an_inclusive_range(self):
        results = _finder(
            "$acme.csvpaths.:last().:from(1):to(3)", STATEMENT_RANGE_MANIFEST
        ).resolve()
        assert [r.identity for r in results.results] == ["1", "2", "3"]
        assert [r.data for r in results.results] == [
            "stmt 1 text",
            "stmt 2 text",
            "stmt 3 text",
        ]

    def test_date_mode_is_rejected_at_the_statement_level(self):
        # unlike the name_one VERSION range, an individual STATEMENT has no
        # arrival time of its own, only the GROUP VERSION it belongs to
        # does.
        with pytest.raises(ReferenceException3):
            _finder(
                '$acme.csvpaths.:last().:from(:date("2026-01-01"))',
                STATEMENT_RANGE_MANIFEST,
            ).query()

    def test_combining_a_literal_identity_with_a_range_is_rejected(self):
        with pytest.raises(ReferenceException3):
            _finder(
                "$acme.csvpaths.:last().0:from(1)", STATEMENT_RANGE_MANIFEST
            ).query()


class TestIdentityLookup:
    # doc lines "### Identity lookup into the selected version's own
    # statements -- by name, or by stringified load-time index for an
    # unnamed statement"
    def test_by_name(self):
        results = _finder("$acme.csvpaths.:last().company_names", ACME_MANIFEST).query()
        assert results.uuids == ["v1-uuid"]

    def test_by_stringified_load_time_index(self):
        results = _finder("$acme.csvpaths.:last().0", ACME_MANIFEST).query()
        assert results.uuids == ["v1-uuid"]


class TestManifestEitherOrder:
    # doc lines "### The version's own manifest entry, either order"
    def test_pointer_then_manifest(self):
        results = _finder("$acme.csvpaths.:last():manifest()", ACME_MANIFEST).resolve()
        assert results.results[0].data == ACME_MANIFEST[1]

    def test_manifest_then_pointer(self):
        # order-insensitivity fix, settled earlier in the references-v3
        # work -- both orders give the identical matched entry.
        results = _finder("$acme.csvpaths.:manifest():last()", ACME_MANIFEST).resolve()
        assert results.results[0].data == ACME_MANIFEST[1]


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


class TestDefinitionAndSubObjects:
    # doc lines "### definition.json and its sub-objects"
    def test_definition_bare(self):
        results = _finder(
            "$acme.csvpaths.:definition()", ACME_MANIFEST, definition=DEFINITION
        ).query()
        assert results.files == [f"{GROUP_HOME}/definition.json"]
        assert results.results[0].uuid is None

    def test_scripts(self):
        results = _finder(
            "$acme.csvpaths.:scripts()", ACME_MANIFEST, definition=DEFINITION
        ).resolve()
        assert results.results[0].data == {"on_complete_all": "notify.sh"}

    def test_webhooks(self):
        results = _finder(
            "$acme.csvpaths.:webhooks()", ACME_MANIFEST, definition=DEFINITION
        ).resolve()
        assert results.results[0].data == {
            "on_complete_valid": {"url": "https://example.com/hook", "headers": []}
        }

    def test_transfers(self):
        results = _finder(
            "$acme.csvpaths.:transfers()", ACME_MANIFEST, definition=DEFINITION
        ).resolve()
        assert results.results[0].data == {
            "company_names": {
                "on_complete_all": [{"file": "data", "transfer_to": "@out"}]
            }
        }

    def test_destinations(self):
        results = _finder(
            "$acme.csvpaths.:destinations()", ACME_MANIFEST, definition=DEFINITION
        ).resolve()
        assert results.results[0].data == {"main": {"address": "example.com", "port": 22}}


LOADS_LEDGER = [
    {"named_paths_name": "acme", "uuid": "u-loads-1"},
    {"named_paths_name": "beta", "uuid": "u-loads-2"},
    {"named_paths_name": "gamma", "uuid": "u-loads-3"},
]


class TestGlobalLoadsLedger:
    # doc line "### Global loads ledger -- every named-paths group's own
    # load, one flat array"
    def test_bare_gives_the_ledger_path_with_no_uuid(self):
        results = _finder(
            "$*.csvpaths.:manifest()",
            ACME_MANIFEST,
            inputs_csvpaths_path="inputs/named_paths",
        ).query()
        assert results.files == ["inputs/named_paths/manifest.json"]
        assert results.results[0].uuid is None


class TestGlobalLoadsLedgerOrdinalIndexing:
    # doc lines "### Ordinal indexing into the global ledger, either order"
    def test_pointer_then_manifest(self):
        results = _finder(
            "$*.csvpaths.:last():manifest()",
            ACME_MANIFEST,
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        ).resolve()
        assert results.results[0].data == LOADS_LEDGER[-1]

    def test_manifest_then_pointer(self):
        results = _finder(
            "$*.csvpaths.:manifest():last()",
            ACME_MANIFEST,
            inputs_csvpaths_path="inputs/named_paths",
            ledger=LOADS_LEDGER,
        ).resolve()
        assert results.results[0].data == LOADS_LEDGER[-1]


#
# two named-paths groups for '*' traversal -- beta listed first in
# STAR_BY_NAME on purpose (naive concatenation with no time-sort would put
# alpha's own last entry last in the pooled list, masking a broken sort).
#
STAR_ALPHA_MANIFEST = [
    {
        "group_file_path": "named_paths/alpha/group.csvpath",
        "uuid": "a-v1",
        "time": "2026-01-01T00:00:00+00:00",
        "named_paths_identities": ["0"],
    },
    {
        "group_file_path": "named_paths/alpha/group.csvpath",
        "uuid": "a-v2",
        "time": "2026-01-02T00:00:00+00:00",
        "named_paths_identities": ["0"],
    },
]
STAR_BETA_MANIFEST = [
    {
        "group_file_path": "named_paths/beta/group.csvpath",
        "uuid": "b-v1",
        "time": "2026-01-03T00:00:00+00:00",
        "named_paths_identities": ["0"],
    },
]
STAR_BY_NAME = {"beta": STAR_BETA_MANIFEST, "alpha": STAR_ALPHA_MANIFEST}


def _star_finder(reference: str) -> CsvpathsReferenceFinder3:
    return _finder(reference, manifest=ACME_MANIFEST, by_name=STAR_BY_NAME)


class TestStarTraversalFlatten:
    # doc line "### \"*\" traversal, FLATTEN -- single true-latest version
    # across every named-paths group"
    def test_last_across_every_group_is_the_true_most_recent(self):
        results = _star_finder("$*.csvpaths.:last()").query()
        assert results.uuids == ["b-v1"]


class TestStarTraversalGroup:
    # doc line "### \"*\" traversal, GROUP -- one result per named-paths
    # group"
    def test_all_with_last_gives_one_result_per_group(self):
        results = _star_finder("$*.csvpaths.:all():last()").query()
        assert set(results.uuids) == {"a-v2", "b-v1"}


class TestStarTraversalUnreduced:
    # doc line "### \"*\" traversal -- every version from every group,
    # unreduced"
    def test_all_with_no_pointer_gives_every_version_unreduced(self):
        results = _star_finder("$*.csvpaths.:all()").query()
        assert set(results.uuids) == {"a-v1", "a-v2", "b-v1"}


#
# a single richly-populated version for the field-accessor section --
# every doc-listed field lives on this one manifest entry.
#
FIELD_ACCESSOR_MANIFEST = [
    {
        "group_file_path": GROUP_FILE_PATH,
        "uuid": "v0-uuid",
        "named_paths": ["stmt A text", "stmt B text"],
        "named_paths_identities": ["company_names", "1"],
        "named_paths_count": 2,
        "named_paths_name": "acme",
        "named_paths_home": GROUP_HOME,
        "time": "2026-01-01T00:00:00+00:00",
        "time_completed": "2026-01-01T00:05:00+00:00",
        "fingerprint": "aaaa",
        "source_path": "/staging/acme",
        "manifest_path": f"{GROUP_HOME}/manifest.json",
    }
]


class TestFieldAccessorsOnOneMatchedVersion:
    # doc lines "### Field accessors on one matched version"
    def test_uuid(self):
        results = _finder(
            "$acme.csvpaths.:last():uuid()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == "v0-uuid"

    def test_time(self):
        results = _finder(
            "$acme.csvpaths.:last():time()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == "2026-01-01T00:00:00+00:00"

    def test_fingerprint(self):
        results = _finder(
            "$acme.csvpaths.:last():fingerprint()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == "aaaa"

    def test_home_reads_named_paths_home(self):
        results = _finder(
            "$acme.csvpaths.:last():home()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == GROUP_HOME

    def test_origin(self):
        results = _finder(
            "$acme.csvpaths.:last():origin()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == "/staging/acme"

    def test_manifest_path(self):
        results = _finder(
            "$acme.csvpaths.:last():manifest_path()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == f"{GROUP_HOME}/manifest.json"

    def test_time_completed(self):
        results = _finder(
            "$acme.csvpaths.:last():time_completed()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == "2026-01-01T00:05:00+00:00"

    def test_named_paths_name(self):
        results = _finder(
            "$acme.csvpaths.:last():named_paths_name()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == "acme"

    def test_named_paths_identities(self):
        results = _finder(
            "$acme.csvpaths.:last():named_paths_identities()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == ["company_names", "1"]

    def test_named_paths_count(self):
        results = _finder(
            "$acme.csvpaths.:last():named_paths_count()", FIELD_ACCESSOR_MANIFEST
        ).resolve()
        assert results.results[0].data == 2
