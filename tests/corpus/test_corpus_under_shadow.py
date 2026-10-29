"""The corpus under [references] sql = shadow (step 5, PR 2).

The committed corpus under tests/corpus/data/ was generated without SQL,
and shadow assumes SQL has mirrored every write from the start (nothing is
backfilled). So this module regenerates the corpus from assets.yaml into a
temp directory with the sql listener group on (SQLite, in the same temp
directory), using generate.py's own build_events() and run_events(). The
committed data is not touched.

References are built from the names in assets.yaml, so they grow with the
corpus. Each must resolve the same under off and shadow, and one shadow
source over all of them must read every ReferenceSource method with no
difference and no SQL error.
"""

import os
import sys
from pathlib import Path

import pytest
import yaml

from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)
from csvpath.references.sources.reference_source import ReferenceSource
from csvpath.references.sources.shadow_reference_source import (
    ShadowReferenceSource,
)
from csvpath.util.box import Box

CORPUS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CORPUS_DIR))

_CONFIG_BEFORE_IMPORT = os.environ.get("CSVPATH_CONFIG_PATH")

import generate  # noqa: E402

#
# importing generate.py must not choose a config. tests/conftest.py's
# session fixture wipes every directory the active config names before the
# first test, and the corpus config names the committed tests/corpus/data/.
# collection runs before that fixture, so restoring the setting and raising
# here stops the run with the corpus intact.
#
if os.environ.get("CSVPATH_CONFIG_PATH") != _CONFIG_BEFORE_IMPORT:
    if _CONFIG_BEFORE_IMPORT is None:
        os.environ.pop("CSVPATH_CONFIG_PATH", None)
    else:
        os.environ["CSVPATH_CONFIG_PATH"] = _CONFIG_BEFORE_IMPORT
    raise RuntimeError(
        "importing tests/corpus/generate.py changed CSVPATH_CONFIG_PATH; "
        "it must only be set in generate.main()"
    )

ASSETS = yaml.safe_load((CORPUS_DIR / "assets.yaml").read_text())
FILE_NAMES = [g["name"] for g in ASSETS["named_files"]]
PATHS_NAMES = [g["name"] for g in ASSETS["named_paths"]]
RESULTS_NAMES = [g["paths_name"] for g in ASSETS["results"]]

FILES = [
    ":all()",
    ":first()",
    ":last()",
    ":index(1)",
    "*/:last()",
    ":flatten()",
    ":flatten().:first()",
    ":flatten().:last()",
    ":groups()",
    ":groups().:last()",
    ":groups().:from(0):to(1)",
    ":groups().:before(:index(1))",
    ":flatten().:after(:index(0))",
    ":flatten().:index(1)",
    ":manifest()",
    ":manifest():last()",
    ':status("failed")',
    ':status("complete").:first()',
    ":last():manifest()",
    ":definition()",
]
CSVPATHS = [
    ":all()",
    ":first()",
    ":last()",
    ":index(1)",
    ":from(-2)",
    ":manifest()",
    ":manifest():last()",
    ":last():manifest()",
    ":last():uuid()",
    ":last():fingerprint()",
    ":last():named_paths_count()",
    ":last():named_paths_identities()",
    ":last():username()",
    ":before(:index(1))",
    ":after(:index(0))",
]
RESULTS = [
    ":all()",
    ":first()",
    ":last()",
    ":all():last()",
    ":manifest()",
    ":last():manifest()",
    ":last().:all()",
    ":last().*",
    ":last().:index(0)",
    ":last().:errors()",
    ":flatten()",
    ":flatten():last()",
    ":flatten():before(:index(2))",
    ":first():named_file_uuid()",
    ":last():named_paths_uuid()",
]
TRAVERSALS = [
    "$*.files.:manifest()",
    "$*.files.:manifest():last()",
    "$*.files.:manifest():uuid()",
    "$*.files.:flatten()",
    "$*.files.:groups().:last()",
    '$*.files.:status("failed")',
    "$:regex(/^o/).files.:all()",
    "$*.csvpaths.:all()",
    "$*.csvpaths.:last()",
    "$*.csvpaths.:manifest()",
    "$*.csvpaths.:manifest():last()",
    "$:regex(/^v/).csvpaths.:last()",
    "$*.results.:last()",
    "$*.results.:manifest()",
    "$*.results.:manifest():last()",
    "$*.results.:manifest():first():run_uuid()",
    "$*.results.:flatten():first():uuid()",
    "$*.results.:flatten():error_count(0)",
    "$:regex(/^s/).results.:flatten()",
]
#
# a name in no datatype, so missing names are compared too
#
MISSING = "nope"

REFERENCES = (
    [f"${n}.files.{s}" for n in FILE_NAMES + [MISSING] for s in FILES]
    + [f"${n}.csvpaths.{s}" for n in PATHS_NAMES + [MISSING] for s in CSVPATHS]
    + [f"${n}.results.{s}" for n in RESULTS_NAMES + [MISSING] for s in RESULTS]
    + TRAVERSALS
)


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _mode(p: CsvPaths, mode: str) -> None:
    p.config.add_to_config(section="references", key="sql", value=mode)


def _resolve(p: CsvPaths, reference: str):
    try:
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        return ("ok", finder.query())
    except Exception as ex:
        return ("raised", type(ex))


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    _clear_engine()
    tmp = tmp_path_factory.mktemp("corpus_under_shadow")
    scratch = tmp / "scratch"
    scratch.mkdir()
    p = CsvPaths()
    c = p.config
    c.add_to_config(section="inputs", key="files", value=str(tmp / "named_files"))
    c.add_to_config(section="inputs", key="csvpaths", value=str(tmp / "named_paths"))
    c.add_to_config(section="results", key="archive", value=str(tmp / "archive"))
    c.add_to_config(section="listeners", key="groups", value="sql")
    c.add_to_config(section="sql", key="dialect", value="sqlite")
    c.add_to_config(
        section="sql", key="connection_string", value=f"sqlite:///{tmp / 'corpus.db'}"
    )
    #
    # generate.py's source paths are relative to the repo root
    #
    cwd = os.getcwd()
    os.chdir(generate.REPO_ROOT)
    try:
        generate.run_events(p, generate.build_events(ASSETS), scratch_dir=scratch)
    finally:
        generate.reset_now()
        os.chdir(cwd)
    _mode(p, "off")
    yield p
    _mode(p, "off")
    _clear_engine()


@pytest.fixture(scope="module")
def off_results(corpus):
    _mode(corpus, "off")
    return {r: _resolve(corpus, r) for r in REFERENCES}


@pytest.fixture(scope="module")
def shadow_run(corpus):
    """every reference resolved under shadow, on one shadow source"""
    _mode(corpus, "shadow")
    try:
        source = corpus.reference_source
        results = {r: _resolve(corpus, r) for r in REFERENCES}
        assert corpus.reference_source is source
    finally:
        _mode(corpus, "off")
    return source, results


# ===================
# the regenerated corpus
# ===================


def test_the_corpus_has_what_assets_yaml_lists(corpus):
    #
    # so a generator change cannot quietly empty the corpus and leave
    # agreement on nothing
    #
    fs = FilesystemReferenceSource(csvpaths=corpus)
    assert fs.file_names() == sorted(FILE_NAMES)
    assert fs.paths_names() == sorted(PATHS_NAMES)
    for group in ASSETS["named_files"]:
        assert len(fs.file_manifest(group["name"])) == len(group["versions"])
    for group in ASSETS["named_paths"]:
        assert len(fs.paths_manifest(group["name"])) == len(group["versions"])
    runs = len([r for g in ASSETS["results"] for r in g["runs"]])
    assert len(fs.run_homes(root_major=None, name_filter=None)) == runs


def test_the_scratch_copies_stay_in_the_temp_directory(corpus):
    assert not (CORPUS_DIR / ".scratch").exists()


def test_most_references_find_something(off_results):
    #
    # parity of empty results or of errors proves little
    #
    found = [r for r, (kind, v) in off_results.items() if kind == "ok" and len(v) > 0]
    assert len(found) >= 0.7 * len(REFERENCES)


# ===================
# off and shadow
# ===================


@pytest.mark.parametrize("reference", REFERENCES)
def test_off_and_shadow_agree(off_results, shadow_run, reference):
    _, shadow = shadow_run
    assert off_results[reference] == shadow[reference]


def test_shadow_finds_no_differences(shadow_run):
    source, _ = shadow_run
    assert isinstance(source, ShadowReferenceSource)
    counts = source.counts
    assert sorted(counts) == sorted(ReferenceSource.__abstractmethods__)
    for method, c in counts.items():
        assert c["reads"] > 0, method
        assert c["differences"] == 0, method
        assert c["sql_errors"] == 0, method
        assert c["matches"] == c["reads"], method


# ===================
# generate.run_events
# ===================


@pytest.mark.parametrize("bad", [None, "scratch", 1])
def test_run_events_checks_the_scratch_dir(bad):
    with pytest.raises(TypeError):
        generate.run_events(None, [], scratch_dir=bad)
