#
# RESULTS name_one wildcards in any path position (name_one gap review,
# 2026-11-19, items B and C): ':groups()' with more path after it
# (compendium 3.20's ':groups()/:from(:index(-2)):to(:index(-1))'),
# ':flatten()' with more path (4.5's ':flatten()/:all()'), ':all()' before
# a ':flatten()', and a middle ':all()' under a '$*' root. All raised "Does
# not yet support :X() as a name_one path segment". Also: a middle ':all()'
# keyed its groups through a '*' after it, where 4.1 says the '*' pools.
#
# The FILES twin is test_files_wildcard_paths_3.py (#787); both use
# ReferenceFinder3._wildcard_segments_key(). In RESULTS the segments are
# the template levels; a trailing '*' or ':all()' is the run dir (4.1a,
# 4.2b).
#
import os
import time

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_finder_3 import ReferenceFinder3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import _config_file

SEP = "\n\n---- CSVPATH ----\n\n"
STATEMENTS = ["~ id: first_id ~ $[*][yes()]", "~ id: second_id ~ $[*][no()]"]

#
# (template, runs), run in this order
#
RUNS = [
    (None, 2),
    ("beta/:run_dir", 3),
    ("gamma/:run_dir", 2),
    ("customers/east/:run_dir", 1),
    ("customers/west/:run_dir", 1),
    ("north/2025/:run_dir", 1),
    ("south/2025/:run_dir", 2),
    ("north/2026/:run_dir", 1),
]


def _run_homes(archive: str) -> set:
    homes = set()
    for root, _, files in os.walk(archive):
        if "manifest.json" in files and os.path.basename(os.path.dirname(root)) != "":
            homes.add(root)
    return homes


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("results_wildcard_paths")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        yield _ran(tmp)
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _ran(tmp) -> tuple:
    p = CsvPaths()
    data = tmp / "orders.csv"
    data.write_text("id,v\n1,2\n", encoding="utf-8")
    p.file_manager.add_named_file(name="orders", path=str(data))
    group = tmp / "acme.csvpaths"
    group.write_text(SEP.join(STATEMENTS), encoding="utf-8")
    home = os.path.join(str(tmp / "archive"), "acme")
    label = {}
    seen = set()
    for i, (template, times) in enumerate(RUNS):
        if i:
            # a run dir is named by the second it started in; runs in
            # different template dirs in one second would tie, and a
            # pointer pooled across dirs ('$acme.results.:flatten()/2025/*
            # :last()') would pick by the tie-break, not by time
            time.sleep(1.05)
        p.paths_manager.add_named_paths_from_file(
            name="acme", file_path=str(group), template=template
        )
        for n in range(times):
            p.collect_paths(pathsname="acme", filename="orders")
            now = {
                h
                for h in _run_homes(home)
                if os.path.basename(h) not in ("first_id", "second_id")
            }
            new = now - seen
            assert len(new) == 1, new
            seen |= new
            run = new.pop()
            where = os.path.dirname(os.path.relpath(run, home))
            label[os.path.realpath(run)] = f"{where or '.'}#{n + 1}"
    return p, label


def _labels(runs, reference: str) -> list:
    p, label = runs
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [label[os.path.realpath(str(r.path))] for r in finder.query().results]


# ===================
# the shared matcher, as RESULTS calls it
# ===================


class TestTemplateLevels:
    def _key(self, segments, elements):
        return ReferenceFinder3._wildcard_segments_key(
            segments=segments, elements=elements, last_deep_min=0
        )

    def test_a_last_any_depth_wildcard_may_match_no_level(self):
        # the run dir follows the template levels
        assert self._key([], [("wild", "groups")]) == ()
        assert self._key([], [("wild", "flatten")]) == ()

    def test_all_then_flatten_needs_the_all_level(self):
        assert self._key([], [("wild", "all"), ("wild", "flatten")]) is None
        assert self._key(["north", "2025"], [("wild", "all"), ("wild", "flatten")]) == (
            "north",
        )

    def test_a_negative_minimum_raises(self):
        with pytest.raises(ValueError):
            ReferenceFinder3._wildcard_segments_key(
                segments=[], elements=[], last_deep_min=-1
            )


# ===================
# end to end
# ===================

GROUPED = {
    # a middle ':all()' keys by its own level; the '*' after it pools (4.1)
    "$acme.results.:all()/*/*:last()": [
        "customers/west#1",
        "north/2026#1",
        "south/2025#2",
    ],
    "$acme.results.:all()/2025/*:last()": ["north/2025#1", "south/2025#2"],
    "$acme.results.customers/:all()/*:last()": ["customers/east#1", "customers/west#1"],
    # B: ':groups()' with a run slot after it is ':groups()'
    "$acme.results.:groups()/*:last()": [
        ".#2",
        "beta#3",
        "customers/east#1",
        "customers/west#1",
        "gamma#2",
        "north/2025#1",
        "north/2026#1",
        "south/2025#2",
    ],
    # compendium 3.20: the last two runs of each group (functions after a
    # '/' imply the run '*', 3.9c)
    "$acme.results.:groups()/:from(:index(-2)):to(:index(-1))": [
        ".#1",
        ".#2",
        "beta#2",
        "beta#3",
        "customers/east#1",
        "customers/west#1",
        "gamma#1",
        "gamma#2",
        "north/2025#1",
        "north/2026#1",
        "south/2025#1",
        "south/2025#2",
    ],
    "$acme.results.:groups()/east/*:last()": ["customers/east#1"],
    # C: ':flatten()' with more path. ':all()' at the run dir is '*' (4.2b),
    # so ':flatten()/:all()' is ':flatten()'
    "$acme.results.:flatten()/:all():last()": ["north/2026#1"],
    "$acme.results.:flatten()/2025/*:last()": ["south/2025#2"],
    "$acme.results.:flatten()/east/*": ["customers/east#1"],
    # ':flatten()' then a grouping level: by the last template level, so
    # north/2025 and south/2025 are one '2025' group
    "$acme.results.:flatten()/:all()/*:last()": [
        "south/2025#2",
        "north/2026#1",
        "beta#3",
        "customers/east#1",
        "gamma#2",
        "customers/west#1",
    ],
    "$acme.results.:all()/:flatten():last()": [
        "beta#3",
        "customers/west#1",
        "gamma#2",
        "north/2026#1",
        "south/2025#2",
    ],
    # a '$*' root: the same, per named-results name; ':flatten()' pools
    "$*.results.:all()/*:last()": ["beta#3", "gamma#2"],
    "$*.results.customers/:all()/*:last()": ["customers/east#1", "customers/west#1"],
    "$*.results.:flatten()/2025/*:last()": ["south/2025#2"],
    "$*.results.:flatten()/:all()/*:last()": [
        "south/2025#2",
        "north/2026#1",
        "beta#3",
        "customers/east#1",
        "gamma#2",
        "customers/west#1",
    ],
}


class TestGroupedReferences:
    @pytest.mark.parametrize("reference", sorted(GROUPED))
    def test_runs(self, runs, reference):
        assert _labels(runs, reference) == GROUPED[reference]

    @pytest.mark.parametrize(
        "written,same_as",
        [
            ("$acme.results.:groups()/*:last()", "$acme.results.:groups():last()"),
            ("$acme.results.:flatten()/:all()", "$acme.results.:flatten()"),
            ("$*.results.:groups()/*:last()", "$*.results.:groups():last()"),
        ],
    )
    def test_equivalent_spellings(self, runs, written, same_as):
        assert _labels(runs, written) == _labels(runs, same_as)

    def test_a_star_root_matches_the_literal_root(self, runs):
        # one named-results name, so '$*' gives what '$acme' gives
        for reference in ("customers/:all()/*:last()", ":flatten()/:all()/*:last()"):
            assert _labels(runs, f"$*.results.{reference}") == _labels(
                runs, f"$acme.results.{reference}"
            )


@pytest.mark.parametrize(
    "reference",
    sorted(GROUPED)
    + [
        "$acme.results.:groups()/*:last().first_id",
        "$acme.results.:flatten()/:all()/*:last():run_uuid()",
        "$*.results.:all()/*:last().first_id:errors()",
    ],
)
def test_the_estimate_keeps_its_contract(runs, reference):
    p, _ = runs
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    est = finder.estimate()
    measured, raised = _measure(p, reference)
    assert _problems(est, measured, raised) == []
