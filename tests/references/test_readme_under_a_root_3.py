#
# a bare ':readme()' under a '*', ':regex()' or ':choice()' root, in FILES
# and CSVPATHS (David, 2026-11-22, decision log D40 g). Compendium 5.8:
# like '$*.files.:definition()', such a reference "will return the
# paths+uuid to the ... files on query() but will raise an error on
# resolve()" (resolving several whole files at once, 5.3); a readme that
# does not exist resolves to None (1113-1118). Both datatypes raised at
# query.
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    CORPUS_CONFIG,
    _measure,
    _problems,
)


@pytest.fixture(scope="module")
def corpus():
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = os.path.abspath(CORPUS_CONFIG)
    try:
        yield CsvPaths()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _finder(*, p, reference: str):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)


def _names(p, datatype: str) -> list:
    if datatype == "files":
        return sorted(p.file_manager.named_file_names)
    return sorted(p.paths_manager.named_paths_names)


def _home(p, datatype: str, name: str) -> str:
    if datatype == "files":
        return p.file_manager.named_file_home(name)
    return p.paths_manager.named_paths_home(name, assure=False)


DATATYPES = ["files", "csvpaths"]


@pytest.mark.parametrize("datatype", DATATYPES)
def test_star_gives_each_readme_path(corpus, datatype):
    names = _names(corpus, datatype)
    assert len(names) > 1
    results = _finder(p=corpus, reference=f"$*.{datatype}.:readme()").query().results
    assert [str(r.path) for r in results] == [
        os.path.join(_home(corpus, datatype, n), "README.md") for n in names
    ]
    assert all(r.uuid is None for r in results)


@pytest.mark.parametrize("datatype", DATATYPES)
def test_several_raise_on_resolve_but_each_resolves(corpus, datatype):
    finder = _finder(p=corpus, reference=f"$*.{datatype}.:readme()")
    selection = finder.query()
    with pytest.raises(ReferenceException3, match="more than one"):
        finder.resolve_from(selection)
    for path, result in zip(selection.results, finder.resolve_each(selection).results):
        if os.path.exists(str(path.path)):
            with open(str(path.path), "rb") as f:
                assert result.data == f.read()
        else:
            assert result.data is None


@pytest.mark.parametrize("datatype", DATATYPES)
def test_a_pattern_root_filters_by_name(corpus, datatype):
    first = _names(corpus, datatype)[0]
    for root in (f"$:regex(/^{first}$/)", f'$:choice("{first}")'):
        finder = _finder(p=corpus, reference=f"{root}.{datatype}.:readme()")
        selection = finder.query()
        assert [str(r.path) for r in selection.results] == [
            os.path.join(_home(corpus, datatype, first), "README.md")
        ]
        # one readme resolves, as the literal root does
        literal = _finder(p=corpus, reference=f"${first}.{datatype}.:readme()")
        assert [r.data for r in finder.resolve_from(selection).results] == [
            r.data for r in literal.resolve_from(literal.query()).results
        ]


@pytest.mark.parametrize("datatype", DATATYPES)
def test_no_match_is_nothing(corpus, datatype):
    assert (
        _finder(p=corpus, reference=f"$:regex(/^zz_none$/).{datatype}.:readme()")
        .query()
        .results
        == []
    )


@pytest.mark.parametrize(
    "reference",
    [
        "$*.files.:readme():last()",
        "$*.files.:readme().:last()",
        "$*.csvpaths.:readme():last()",
    ],
)
def test_a_combination_still_raises(corpus, reference):
    with pytest.raises(ReferenceException3, match="readme"):
        _finder(p=corpus, reference=reference).query()


@pytest.mark.parametrize("datatype", DATATYPES)
@pytest.mark.parametrize("root", ["$*", "$:regex(/./)", '$:choice("nope")'])
def test_the_estimate_keeps_its_contract(corpus, datatype, root):
    reference = f"{root}.{datatype}.:readme()"
    measured, raised = _measure(corpus, reference)
    assert (
        _problems(_finder(p=corpus, reference=reference).estimate(), measured, raised)
        == []
    )


# ===================
# deleted entities and a missing readme (reviewer on #804)
# ===================


@pytest.fixture(scope="module")
def pruned(tmp_path_factory):
    # files a, b, c, d and groups ga, gb, gc, gd; d and gd are removed, and
    # b's and gb's README.md are deleted
    from tests.references.test_files_wildcard_paths_3 import _config_file

    tmp = tmp_path_factory.mktemp("readme_pruned")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        for name in ("a", "b", "c", "d"):
            src = tmp / "src" / name
            src.mkdir(parents=True)
            (src / "x.csv").write_text("id\n1\n", encoding="utf-8")
            p.file_manager.add_named_file(name=name, path=str(src / "x.csv"))
            p.paths_manager.add_named_paths(name=f"g{name}", paths=["$[*][yes()]"])
        p.file_manager.remove_named_file("d")
        p.paths_manager.remove_named_paths("gd")
        for home in (
            p.file_manager.named_file_home("b"),
            p.paths_manager.named_paths_home("gb", assure=False),
        ):
            readme = os.path.join(home, "README.md")
            if os.path.exists(readme):
                os.remove(readme)
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


PREFIX = {"files": "", "csvpaths": "g"}


@pytest.mark.parametrize("datatype", DATATYPES)
def test_only_live_names_are_listed(pruned, datatype):
    homes = [
        os.path.dirname(str(r.path))
        for r in _finder(p=pruned, reference=f"$*.{datatype}.:readme()").query().results
    ]
    assert [os.path.basename(h) for h in homes] == [
        PREFIX[datatype] + n for n in ("a", "b", "c")
    ]


@pytest.mark.parametrize("datatype", DATATYPES)
def test_a_missing_readme_resolves_to_none(pruned, datatype):
    finder = _finder(p=pruned, reference=f"$*.{datatype}.:readme()")
    data = [r.data for r in finder.resolve_each(finder.query()).results]
    assert data[1] is None
    assert data[0] is not None and data[2] is not None


@pytest.mark.parametrize("datatype", DATATYPES)
def test_a_pattern_that_matches_one_live_name_resolves(pruned, datatype):
    # 'b|d' matches b and the deleted d: one file, so resolve does not raise
    reference = f"$:regex(/^{PREFIX[datatype]}(b|d)$/).{datatype}.:readme()"
    finder = _finder(p=pruned, reference=reference)
    assert [r.data for r in finder.resolve_from(finder.query()).results] == [None]


@pytest.mark.parametrize("datatype", DATATYPES)
@pytest.mark.parametrize(
    "root",
    [
        "$*",
        "$:regex(/^g?(b|d)$/)",
        "$:regex(/^g?(a|b)$/)",
        '$:choice("d")',
        '$:choice("gd")',
    ],
)
def test_the_estimate_keeps_its_contract_when_pruned(pruned, datatype, root):
    reference = f"{root}.{datatype}.:readme()"
    measured, raised = _measure(pruned, reference)
    assert (
        _problems(_finder(p=pruned, reference=reference).estimate(), measured, raised)
        == []
    )


def test_a_csvpaths_combination_says_readme_must_stand_alone(pruned):
    for reference in ("$*.csvpaths.:readme():last()", "$*.csvpaths.:readme().step"):
        with pytest.raises(
            ReferenceException3, match="must be the entire, sole content"
        ):
            _finder(p=pruned, reference=reference).query()
