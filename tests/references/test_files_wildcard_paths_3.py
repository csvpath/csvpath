#
# FILES name_one wildcards in any path position (name_one gap review,
# 2026-11-19, items A, B, C0): ':all()' and ':groups()' as path segments,
# ':flatten()' with more path under a '$*'/':regex()' root, and a name_one
# pointer after a lone wildcard (':all():last()'). All of these raised "Does
# not yet support :X() as a name_one path segment" until then.
#
# The spec: compendium 4.1 ('*' pools its position), 4.1b ('$*' groups per
# named-file; ':flatten()' pools across them), 4.2 (a grouping wildcard
# groups by "the names found at the grouping segment", a pointer after it
# picks within each group), 4.3c (':flatten()' last stands for a file home
# with a template), 4.5 (the legal combinations), NRE 441-472 (the
# ':groups()/*' worked example). Decision D33: the key of ':all()' in the
# last position is a file home name.
#
# The low-level tests check the matcher alone; the rest register a real
# layout and run the references end to end, with the estimate's contract
# checked on each.
#
import configparser
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_3 import Star3
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_3 import ReferenceFinder3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_parser_3 import ReferenceParser3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)

HOME = "inputs/named_files/acme"


def _entry(rel: str) -> dict:
    return {"file_home": f"{HOME}/{rel}"}


def _key(rel: str, elements: list):
    return FilesReferenceFinder3._wildcard_path_key(
        entry=_entry(rel), home=HOME, elements=elements
    )


ALL = ("wild", "all")
GROUPS = ("wild", "groups")
FLATTEN = ("wild", "flatten")
STAR = ("segment", Star3())


def _lit(name: str) -> tuple:
    return ("segment", name)


# ===================
# the matcher alone
# ===================


class TestWildcardPathKey:
    def test_all_then_star_keys_by_the_first_level_and_pools_the_file_home(self):
        assert _key("EMEA/two.csv", [ALL, STAR]) == ("EMEA",)
        assert _key("APAC/five.csv", [ALL, STAR]) == ("APAC",)

    def test_all_then_star_needs_exactly_two_levels(self):
        assert _key("two.csv", [ALL, STAR]) is None
        assert _key("a/b/two.csv", [ALL, STAR]) is None

    def test_a_star_is_never_part_of_the_key(self):
        # 4.1: '*' pools its position
        assert _key("x/jan/week1.csv", [STAR, ALL, STAR]) == ("jan",)

    def test_all_last_keys_by_the_file_home_name(self):
        # D33: EMEA/two.csv and APAC/two.csv are one group
        assert _key("EMEA/two.csv", [STAR, ALL]) == ("two.csv",)
        assert _key("APAC/two.csv", [STAR, ALL]) == ("two.csv",)

    def test_a_literal_prefix_must_match(self):
        assert _key("shipments/jan/week1.csv", [_lit("shipments"), ALL, STAR]) == (
            "jan",
        )
        assert _key("invoices/jan/x.csv", [_lit("shipments"), ALL, STAR]) is None

    def test_groups_then_star_keys_by_every_directory_above_the_file_home(self):
        # NRE 445-462
        assert _key("feb.csv", [GROUPS, STAR]) == ()
        assert _key("invoices/jan/invoice2.csv", [GROUPS, STAR]) == ("invoices", "jan")

    def test_groups_last_keys_by_the_rest_of_the_path(self):
        assert _key("shipments/feb/week1.csv", [STAR, GROUPS]) == ("feb", "week1.csv")
        # the last any-depth wildcard stands for the file home too
        assert _key("feb.csv", [STAR, GROUPS]) is None

    def test_flatten_then_all_keys_by_the_file_home_name_at_any_depth(self):
        assert _key("feb.csv", [FLATTEN, ALL]) == ("feb.csv",)
        assert _key("shipments/feb/week1.csv", [FLATTEN, ALL]) == ("week1.csv",)

    def test_all_then_flatten_keys_by_the_first_level(self):
        assert _key("shipments/feb/week1.csv", [ALL, FLATTEN]) == ("shipments",)
        # ':flatten()' last needs at least the file home after the ':all()'
        assert _key("feb.csv", [ALL, FLATTEN]) is None

    def test_flatten_without_a_grouping_wildcard_matches_with_an_empty_key(self):
        # '*/:flatten()' is the file homes with a template (4.3c)
        assert _key("orders/2026/four.csv", [STAR, FLATTEN]) == ()
        assert _key("three.csv", [STAR, FLATTEN]) is None

    def test_a_file_home_outside_the_named_file_does_not_match(self):
        entry = {"file_home": "inputs/named_files/other/EMEA/two.csv"}
        assert (
            FilesReferenceFinder3._wildcard_path_key(
                entry=entry, home=HOME, elements=[ALL, STAR]
            )
            is None
        )

    def test_none_arguments_raise(self):
        with pytest.raises(ValueError):
            FilesReferenceFinder3._wildcard_path_key(entry=None, home=HOME, elements=[])
        with pytest.raises(ValueError):
            FilesReferenceFinder3._wildcard_path_key(
                entry=_entry("a"), home=None, elements=[]
            )
        with pytest.raises(ValueError):
            FilesReferenceFinder3._wildcard_path_key(
                entry=_entry("a"), home=HOME, elements=None
            )


class TestGroupsOf:
    def test_groups_come_in_key_order_and_keep_their_order(self):
        rows = [{"k": "b", "n": 1}, {"k": "a", "n": 2}, {"k": "b", "n": 3}]
        groups = FilesReferenceFinder3._groups_of(
            candidates=rows, group_key=lambda e: e["k"]
        )
        assert [[r["n"] for r in g] for g in groups] == [[2], [1, 3]]

    def test_none_arguments_raise(self):
        with pytest.raises(ValueError):
            FilesReferenceFinder3._groups_of(candidates=None, group_key=len)
        with pytest.raises(ValueError):
            FilesReferenceFinder3._groups_of(candidates=[], group_key=None)


@pytest.fixture(scope="module")
def plain_csvpaths():
    return CsvPaths()


class TestWhichPathsTheMatcherTakes:
    @pytest.mark.parametrize(
        "name_one,flatten_paths,expected",
        [
            (":all()/*", False, True),
            ("orders/:all()/*", False, True),
            ("*/:groups()", False, True),
            (":flatten()/:all()", False, True),
            (":all():last()", False, True),
            (":flatten():last()", False, True),
            # the bare forms keep their own branches
            (":all()", False, False),
            (":groups()", False, False),
            (":flatten()", True, False),
            # a literal root has its own ':flatten()' path branches
            ("*/:flatten()", False, False),
            ("*/:flatten()", True, True),
            ("orders/*", True, False),
        ],
    )
    def test_shapes(self, plain_csvpaths, name_one, flatten_paths, expected):
        parsed = ReferenceParser3(
            string=f"$acme.files.{name_one}", csvpaths=plain_csvpaths
        ).parsed
        assert (
            FilesReferenceFinder3._is_wildcard_path_reference(
                name_one=parsed.name_one, flatten_paths=flatten_paths
            )
            is expected
        )

    @pytest.mark.parametrize(
        "reference",
        [
            "$acme.files.:flatten()/:groups()",
            "$acme.files.:groups()/:flatten()",
            "$acme.results.:flatten()/:groups()",
            "$acme.results.:groups():flatten()",
        ],
    )
    def test_flatten_and_groups_never_combine(self, plain_csvpaths, reference):
        parsed = ReferenceParser3(string=reference, csvpaths=plain_csvpaths).parsed
        with pytest.raises(ReferenceException3, match="cannot be combined"):
            ReferenceFinder3._check_wildcards(parsed)


# ===================
# end to end, on a real layout
# ===================

#
# (named-file, directories, file name, versions), registered in this order
#
NAMES = ("acme", "alpha", "beta", "cappa", "delta")

LAYOUT = [
    ("alpha", "", "zero.csv", 1),
    ("alpha", "", "one.csv", 2),
    ("beta", "EMEA", "two.csv", 2),
    ("beta", "APAC", "two.csv", 2),
    ("beta", "APAC", "five.csv", 1),
    ("cappa", "", "three.csv", 1),
    ("cappa", "orders/2026", "four.csv", 2),
    ("acme", "", "jan.csv", 2),
    ("acme", "", "feb.csv", 2),
    ("acme", "invoices/jan", "invoice1.csv", 2),
    ("acme", "invoices/jan", "invoice2.csv", 2),
    ("acme", "shipments/jan", "week1.csv", 2),
    ("acme", "shipments/jan", "week2.csv", 2),
    ("acme", "shipments/feb", "week1.csv", 2),
    ("acme", "shipments/feb", "week2.csv", 2),
    # a file home name another named-file has too, registered last
    ("delta", "west", "two.csv", 1),
]


def _config_file(tmp) -> str:
    """the suite's config with this layout's homes, no listeners and no
    manifest cache. Without the cache setting a CsvPaths keeps the
    manifests it reads or writes in memory, so the estimate's read counts
    could not be checked; the corpus config turns it off too. It is read
    when a CsvPaths starts, so it goes in the file."""
    config = configparser.RawConfigParser()
    config.read(os.environ["CSVPATH_CONFIG_PATH"])
    path = tmp / "config.ini"
    settings = {
        # the suite config's own path key points back at it
        ("config", "path"): str(path),
        ("inputs", "files"): str(tmp / "named_files"),
        ("inputs", "csvpaths"): str(tmp / "named_paths"),
        ("results", "archive"): str(tmp / "archive"),
        ("listeners", "groups"): "",
        ("cache", "use_cache"): "no",
    }
    for (section, key), value in settings.items():
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, value)
    with open(path, "w", encoding="utf-8") as f:
        config.write(f)
    return str(path)


@pytest.fixture(scope="module")
def layout(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("files_wildcard_paths")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        yield _registered(tmp)
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _registered(tmp) -> tuple:
    p = CsvPaths()
    n = 0
    for name, dirs, filename, versions in LAYOUT:
        for v in range(versions):
            n += 1
            src = tmp / "src" / str(n)
            src.mkdir(parents=True)
            data = src / filename
            data.write_text(f"id,v\n{n},{v}\n", encoding="utf-8")
            template = f"{dirs}/:filename" if dirs else None
            p.file_manager.add_named_file(name=name, path=str(data), template=template)
    label = {}
    for name in NAMES:
        seen = {}
        for e in p.file_manager.get_manifest(name):
            rel = e["file_home"].split(f"/named_files/{name}/", 1)[1]
            seen[rel] = seen.get(rel, 0) + 1
            label[e["uuid"]] = f"{name}:{rel}#{seen[rel]}"
    return p, label


def _labels(layout, reference: str) -> list:
    p, label = layout
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [label[r.uuid] for r in finder.query().results]


def _homes(layout, reference: str) -> list:
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [str(r.path).split("/named_files/", 1)[1] for r in finder.query().results]


#
# each reference, and the versions it gives, in result order
#
GROUPED = {
    # A: ':all()' as a segment
    "$beta.files.:all()/*.:last()": ["beta:APAC/five.csv#1", "beta:EMEA/two.csv#2"],
    "$acme.files.shipments/:all()/*.:last()": [
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week2.csv#2",
    ],
    "$acme.files.*/:all()/*.:last()": [
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week2.csv#2",
    ],
    # D33: one group per file home name
    "$beta.files.*/:all().:last()": ["beta:APAC/five.csv#1", "beta:APAC/two.csv#2"],
    '$beta.files.:all()/:name("two.csv").:last()': [
        "beta:APAC/two.csv#2",
        "beta:EMEA/two.csv#2",
    ],
    # 4.5: flatten every level except one last grouping level
    "$acme.files.:flatten()/:all().:last()": [
        "acme:feb.csv#2",
        "acme:invoices/jan/invoice1.csv#2",
        "acme:invoices/jan/invoice2.csv#2",
        "acme:jan.csv#2",
        "acme:shipments/feb/week1.csv#2",
        "acme:shipments/feb/week2.csv#2",
    ],
    "$acme.files.:all()/:flatten().:last()": [
        "acme:invoices/jan/invoice2.csv#2",
        "acme:shipments/feb/week2.csv#2",
    ],
    "$acme.files.:flatten()/:all()/*.:last()": [
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week2.csv#2",
    ],
    # B: ':groups()' as a segment -- NRE 445-462's worked example, exactly
    "$acme.files.:groups()/*.:last()": [
        "acme:feb.csv#2",
        "acme:invoices/jan/invoice2.csv#2",
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week2.csv#2",
    ],
    "$acme.files.:groups()/*.:from(0):to(0)": [
        "acme:jan.csv#1",
        "acme:invoices/jan/invoice1.csv#1",
        "acme:shipments/feb/week1.csv#1",
        "acme:shipments/jan/week1.csv#1",
    ],
    "$acme.files.shipments/:groups().:last()": [
        "acme:shipments/feb/week1.csv#2",
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week1.csv#2",
        "acme:shipments/jan/week2.csv#2",
    ],
    # a '$*' root groups within each named-file (4.1b)
    "$*.files.:groups()/*.:last()": [
        "acme:feb.csv#2",
        "acme:invoices/jan/invoice2.csv#2",
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week2.csv#2",
        "alpha:one.csv#2",
        "beta:APAC/five.csv#1",
        "beta:EMEA/two.csv#2",
        "cappa:three.csv#1",
        "cappa:orders/2026/four.csv#2",
        "delta:west/two.csv#1",
    ],
    "$:regex(/^(acme|beta)$/).files.*/:all().:last()": [
        "beta:APAC/five.csv#1",
        "beta:APAC/two.csv#2",
    ],
    # a name_one pointer after a wildcard (4.2, 6.27d)
    "$acme.files.:all():last()": ["acme:feb.csv#2", "acme:jan.csv#2"],
    "$acme.files.:groups()/*:last()": [
        "acme:feb.csv#2",
        "acme:invoices/jan/invoice2.csv#2",
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week2.csv#2",
    ],
    "$acme.files.:flatten():last()": ["acme:shipments/feb/week2.csv#2"],
    # ':flatten()' pools every named-file (4.1b)
    "$*.files.:flatten():last()": ["delta:west/two.csv#1"],
    "$*.files.*/:flatten().:last()": ["delta:west/two.csv#1"],
    # ':flatten()' pools across named-files (4.1b), so one 'two.csv' group
    # spans beta and delta; without it a '$*' group stays in its named-file
    '$*.files.:flatten()/:name("two.csv").:last()': ["delta:west/two.csv#1"],
    "$:regex(/^(beta|delta)$/).files.:flatten()/:all().:last()": [
        "beta:APAC/five.csv#1",
        "delta:west/two.csv#1",
    ],
    "$:regex(/^(beta|delta)$/).files.:flatten()/:all().:first()": [
        "beta:APAC/five.csv#1",
        "beta:EMEA/two.csv#1",
    ],
    "$:regex(/^(beta|delta)$/).files.*/:all().:last()": [
        "beta:APAC/five.csv#1",
        "beta:APAC/two.csv#2",
        "delta:west/two.csv#1",
    ],
    # a middle ':groups()' may match no level at all
    "$beta.files.*/:groups()/*.:last()": ["beta:APAC/five.csv#1"],
    # pattern and clock segments beside a wildcard
    "$acme.files.:regex(/^ship/)/:all()/*.:last()": [
        "acme:shipments/feb/week2.csv#2",
        "acme:shipments/jan/week2.csv#2",
    ],
    # the ':all()' is the second level, so 'invoices/jan' and
    # 'shipments/jan' are one 'jan' group: the ':choice()' level pools (4.1)
    '$acme.files.:choice("invoices|shipments")/:all()/*.:first()': [
        "acme:shipments/feb/week1.csv#1",
        "acme:invoices/jan/invoice1.csv#1",
    ],
    # a named-file with only 0-level file homes: one group
    "$alpha.files.:groups()/*.:last()": ["alpha:one.csv#2"],
    # name_three after the new shapes: a time window, a gate, a range
    "$beta.files.:all()/*.:today():last()": [
        "beta:APAC/five.csv#1",
        "beta:EMEA/two.csv#2",
    ],
    '$beta.files.:all()/*.:type("csv"):first()': [
        "beta:APAC/two.csv#1",
        "beta:EMEA/two.csv#1",
    ],
    "$beta.files.:all()/*.:from(:index(-2))": [
        "beta:APAC/two.csv#2",
        "beta:APAC/five.csv#1",
        "beta:EMEA/two.csv#1",
        "beta:EMEA/two.csv#2",
    ],
    # ':manifest()' after a wildcard path: each matched version's entry,
    # as '*:manifest()' gives
    "$beta.files.:all()/*:manifest()": [
        "beta:EMEA/two.csv#1",
        "beta:EMEA/two.csv#2",
        "beta:APAC/two.csv#1",
        "beta:APAC/two.csv#2",
        "beta:APAC/five.csv#1",
    ],
}


class TestGroupedReferences:
    @pytest.mark.parametrize("reference", sorted(GROUPED))
    def test_versions(self, layout, reference):
        assert _labels(layout, reference) == GROUPED[reference]

    @pytest.mark.parametrize(
        "pointer,dotted",
        [
            ("$acme.files.:all():last()", "$acme.files.:all().:last()"),
            ("$*.files.:all():last()", "$*.files.:all().:last()"),
            ("$*.files.:groups():first()", "$*.files.:groups().:first()"),
            ("$acme.files.:flatten():last()", "$acme.files.:flatten().:last()"),
        ],
    )
    def test_a_name_one_pointer_picks_what_the_name_three_pointer_picks(
        self, layout, pointer, dotted
    ):
        assert _labels(layout, pointer) == _labels(layout, dotted)

    def test_a_star_root_matches_the_literal_roots_together(self, layout):
        literal = []
        for name in NAMES:
            literal += _labels(layout, f"${name}.files.:groups()/*.:last()")
        assert _labels(layout, "$*.files.:groups()/*.:last()") == literal

    def test_no_name_three_gives_the_file_homes(self, layout):
        assert _homes(layout, "$beta.files.:all()/*") == [
            "beta/EMEA/two.csv",
            "beta/APAC/two.csv",
            "beta/APAC/five.csv",
        ]

    @pytest.mark.parametrize(
        "reference",
        [
            "$beta.files.:all()/*#Sheet1.:last()",
            "$beta.files.*/:all()#Sheet1.:last()",
            "$beta.files.*/:groups()#Sheet1.:last()",
            "$acme.files.:flatten()/:all()#Sheet1.:last()",
        ],
    )
    def test_a_worksheet_applies_to_each_group_whatever_the_wildcard_position(
        self, layout, reference
    ):
        # one rule wherever the wildcard is in a path: until review one in
        # the first segment raised and one later did not (reviewer on #787)
        p, _ = layout
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        results = finder.query().results
        assert results and {r.identity for r in results} == {"Sheet1"}

    @pytest.mark.parametrize(
        "reference,count",
        [
            # no wildcard, but a function first in a longer path: these
            # raised on main while '*/:year()/*#Sheet1' and
            # 'orders/:flatten()#Sheet1' did not (reviewer on #787, round 2)
            ("$cappa.files.:flatten()/2026/*#Sheet1.:last()", 1),
            ("$acme.files.:year()/*#Sheet1.:last()", 0),
        ],
    )
    def test_a_function_first_in_a_longer_path_takes_a_worksheet(
        self, layout, reference, count
    ):
        p, _ = layout
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        results = finder.query().results
        assert len(results) == count
        assert all(r.identity == "Sheet1" for r in results)

    @pytest.mark.parametrize(
        "reference",
        ["$beta.files.:manifest()#Sheet1", "$acme.files.:all()#Sheet1.:last()"],
    )
    def test_a_lone_function_has_no_file_for_a_worksheet(self, layout, reference):
        # a function that is the whole of name_one; test_files_reference_
        # finder_3's TestNameTwoWorksheetMarker pins ':all()#hello.:last()'
        p, _ = layout
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        with pytest.raises(ReferenceException3, match="#worksheet"):
            finder.query()

    def test_a_grouping_wildcard_with_an_all_function_raises(self, layout):
        p, _ = layout
        for reference in ("$acme.files.:flatten():all()", "$*.files.:flatten():all()"):
            finder = ReferenceFinderFactory3.for_reference(
                reference=reference, csvpaths=p
            )
            with pytest.raises(
                ReferenceException3, match="attached directly to name_one"
            ):
                finder.query()


class TestFlattenPathsUnderATraversalRoot:
    # gap review C0: the literal root worked, '$*' and ':regex()' raised
    def test_star_root(self, layout):
        # pooled across named-files (4.1b), so in arrival order
        assert sorted(_homes(layout, "$*.files.*/:flatten()")) == sorted(
            h for name in NAMES for h in _homes(layout, f"${name}.files.*/:flatten()")
        )

    def test_regex_root(self, layout):
        assert _homes(layout, "$:regex(/^c/).files.*/:flatten()") == [
            "cappa/orders/2026/four.csv"
        ]

    def test_a_suffix_after_flatten(self, layout):
        assert _homes(layout, '$*.files.:flatten()/:name("two.csv")') == [
            "beta/EMEA/two.csv",
            "beta/APAC/two.csv",
            "delta/west/two.csv",
        ]


# ===================
# the estimate keeps its contract on every shape here
# ===================


ESTIMATED = sorted(GROUPED) + [
    "$acme.files.:groups().:last()",
    "$*.files.:groups().:last()",
    "$cappa.files.orders/:flatten():last()",
    "$acme.files.:flatten():all()",
    "$acme.files.:groups()/*.:last():uuid()",
    "$beta.files.:all()/*",
    "$*.files.*/:flatten()",
    "$*.files.:all():last()",
    "$*.files.:groups():first()",
    "$*.files.:groups()/*:last()",
    "$*.files.*/:all():last()",
    "$beta.files.*/:all():last()",
]


@pytest.mark.parametrize("reference", ESTIMATED)
def test_the_estimate_keeps_its_contract(layout, reference):
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    est = finder.estimate()
    measured, raised = _measure(p, reference)
    assert _problems(est, measured, raised) == []
