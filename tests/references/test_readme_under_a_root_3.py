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
