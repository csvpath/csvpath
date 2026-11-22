#
# a FILES reference to a named-file that does not exist finds nothing and
# does not raise (David, 2026-11-22, decision log D40 f: "A reference query
# that doesn't find results does not raise"; compendium 5.3). It raised
# "ValueError: No manifest for file named nope"; CSVPATHS and RESULTS
# already gave [].
#
import os

import pytest

from csvpath import CsvPaths

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import (  # noqa: F401
    _config_file,
    layout,
)

EMPTY = [
    "$nope.files.:last()",
    "$nope.files.:first()",
    "$nope.files.:all()",
    "$nope.files.*",
    "$nope.files.*.:last()",
    "$nope.files.:all().:last()",
    "$nope.files.:groups().:last()",
    "$nope.files.:flatten().:last()",
    "$nope.files.orders/:last()",
    '$nope.files.:name("x.csv").:last()',
    '$nope.files.:name("x.csv")#sheet1',
    "$nope.files.:manifest():last()",
    '$nope.files.:fingerprint("x")',
    '$nope.files.:uuid("x")',
    '$nope.files.:status("complete")',
    "$nope.files.*.:yesterday()",
    '$nope.files.:status("complete").:last()',
    '$nope.files.*.:status("complete")',
    '$nope.files.:all().:status("complete")',
    "$nope.files.*.:manifest()",
    "$nope.files.:last():manifest()",
    "$nope.files.:all().:last():fingerprint()",
]


def _finder(*, p, reference: str):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)


@pytest.mark.parametrize("reference", EMPTY)
def test_it_finds_nothing_and_does_not_raise(layout, reference):  # noqa: F811
    p, _ = layout
    finder = _finder(p=p, reference=reference)
    selection = finder.query()
    assert selection.results == []
    assert finder.resolve_from(selection).results == []


# the well-known files are paths whatever exists, as CSVPATHS gives for a
# missing group ('$nope.csvpaths.:readme()'); a missing file resolves to None
WELL_KNOWN = [
    ("$nope.files.:manifest()", "manifest.json"),
    ("$nope.files.:readme()", "README.md"),
    ("$nope.files.:definition()", "definition.json"),
]

# estimates that say "may raise" on a live name too (over-approximations the
# contract allows): a bare argued selector, fixed with the 6.19 list form, and
# the loose "several functions on name_one" rule
SAYS_MAY_RAISE_ON_ANY_NAME = {
    '$nope.files.:fingerprint("x")',
    '$nope.files.:uuid("x")',
    "$nope.files.:last():manifest()",
}


@pytest.mark.parametrize("reference,filename", WELL_KNOWN)
def test_a_well_known_file_is_a_path_to_nothing(layout, reference, filename):  # noqa: F811
    p, _ = layout
    finder = _finder(p=p, reference=reference)
    selection = finder.query()
    assert [str(r.path).rsplit("/", 1)[-1] for r in selection.results] == [filename]
    assert [r.data for r in finder.resolve_from(selection).results] == [None]


@pytest.mark.parametrize("reference", EMPTY + [r for r, _ in WELL_KNOWN])
def test_the_estimate_does_not_predict_a_raise(layout, reference):  # noqa: F811
    p, _ = layout
    measured, raised = _measure(p, reference)
    assert raised is None
    estimate = _finder(p=p, reference=reference).estimate()
    assert _problems(estimate, measured, raised) == []
    if reference not in SAYS_MAY_RAISE_ON_ANY_NAME:
        assert not estimate.would_raise, estimate.would_raise


def test_a_live_named_file_still_answers(layout):  # noqa: F811
    p, _ = layout
    assert _finder(p=p, reference="$alpha.files.:all()").query().results


@pytest.mark.parametrize(
    "shape",
    [
        ".files.:last().:last()",
        '.files.:status("x"):fingerprint()',
        ".files.:fingerprint()",
    ],
)
def test_an_illegal_shape_raises_whether_or_not_the_name_exists(layout, shape):  # noqa: F811
    # the shape is checked before any manifest is read
    p, _ = layout
    messages = []
    for root in ("$alpha", "$nope"):
        with pytest.raises(ReferenceException3) as e:
            _finder(p=p, reference=root + shape).query()
        messages.append(str(e.value))
    assert messages[0] == messages[1]


# ===================
# a named-file registered, then removed: still in the ledger, no manifest
# (reviewer on #803: the estimate charged an exact read that never happens)
# ===================


@pytest.fixture(scope="module")
def removed(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("missing_named_file_removed")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        for name in ("keep", "gone"):
            src = tmp / "src" / name
            src.mkdir(parents=True)
            (src / "x.csv").write_text("id\n1\n", encoding="utf-8")
            p.file_manager.add_named_file(name=name, path=str(src / "x.csv"))
        p.file_manager.remove_named_file("gone")
        # an interrupted registration: a home folder, no manifest.json
        os.makedirs(os.path.join(p.config.inputs_files_path, "half"))
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _gone(reference: str, name: str = "gone") -> str:
    return reference.replace("$nope", f"${name}", 1)


@pytest.mark.parametrize("name", ["gone", "half"])
@pytest.mark.parametrize("reference", EMPTY)
def test_a_removed_name_finds_nothing(removed, reference, name):
    finder = _finder(p=removed, reference=_gone(reference, name))
    selection = finder.query()
    assert selection.results == []
    assert finder.resolve_from(selection).results == []


@pytest.mark.parametrize("name", ["gone", "half"])
@pytest.mark.parametrize("reference", EMPTY + [r for r, _ in WELL_KNOWN])
def test_a_removed_name_keeps_the_estimate_contract(removed, reference, name):
    # 'half' is a home folder with no manifest.json (reviewer on #803)
    reference = _gone(reference, name)
    measured, raised = _measure(removed, reference)
    assert raised is None
    estimate = _finder(p=removed, reference=reference).estimate()
    assert _problems(estimate, measured, raised) == []


def test_the_live_name_beside_it_still_answers(removed):
    assert _finder(p=removed, reference="$keep.files.:all()").query().results
