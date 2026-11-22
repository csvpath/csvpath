#
# a '#worksheet' marker with no version pointer (name_one gap review, item
# H). NRE '$acme.files.orders/:name("west coast.xlsx")#march': "the
# reference result returned on query() is the typical path+uuid plus the
# name_two value". A file home has a path and no uuid, and resolves to None
# (5.21 "name_one, no pointer"); with the marker each file home carries the
# worksheet as its identity. It raised "requires a version-selecting
# pointer". A pointer in name_three reads the sheet, as before.
#
import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import layout  # noqa: F401


def _rows(p, reference: str) -> list:
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [(str(r.path), r.uuid, r.identity) for r in finder.query().results]


@pytest.mark.parametrize(
    "plain",
    ['$beta.files.EMEA/:name("two.csv")', "$alpha.files.*", "$beta.files.:all()/*"],
)
def test_the_file_homes_with_the_worksheet_as_identity(layout, plain):  # noqa: F811
    p, _ = layout
    without = _rows(p, plain)
    with_marker = _rows(p, plain + "#march")
    assert without and [(path, uuid) for path, uuid, _ in with_marker] == [
        (path, uuid) for path, uuid, _ in without
    ]
    assert {identity for _, _, identity in with_marker} == {"march"}
    assert all(uuid is None for _, uuid, _ in with_marker)


def test_resolve_is_none_as_for_a_file_home(layout):  # noqa: F811
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(
        reference='$beta.files.EMEA/:name("two.csv")#march', csvpaths=p
    )
    assert [r.data for r in finder.resolve_from(finder.query()).results] == [None]


def test_a_pointer_still_reads_a_version(layout):  # noqa: F811
    # the version, with the worksheet; reading it needs an XLSX file, and
    # these are CSVs, so resolve raises as before
    p, _ = layout
    rows = _rows(p, '$beta.files.EMEA/:name("two.csv")#march.:last()')
    assert len(rows) == 1 and rows[0][1] is not None and rows[0][2] == "march"


def test_a_name_three_without_a_pointer_still_raises(layout):  # noqa: F811
    # no example asks for several versions with a worksheet
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(
        reference='$beta.files.EMEA/:name("two.csv")#march.:from(0)', csvpaths=p
    )
    with pytest.raises(ReferenceException3, match="version-selecting pointer"):
        finder.query()


@pytest.mark.parametrize(
    "reference",
    ['$beta.files.EMEA/:name("two.csv")#march', "$alpha.files.*#march"],
)
def test_the_estimate_keeps_its_contract(layout, reference):  # noqa: F811
    p, _ = layout
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    measured, raised = _measure(p, reference)
    assert _problems(finder.estimate(), measured, raised) == []
