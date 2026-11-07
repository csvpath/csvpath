"""ProjectRulesbase: where a project's rulesbase is, and the catalog it
gives (specs/macie/rulesbase-design.md, P1 and P3). The project opts in by
creating <rulesbase>/macie; without it nothing is read or written."""

import json
import os

import pytest

from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.project_rulesbase import ProjectRulesbase


class FakeConfig:
    """just the get() ProjectRulesbase uses"""

    def __init__(self, values: dict) -> None:
        self.values = values

    def get(self, *, section: str, name: str, default=None):
        return self.values.get((section, name), default)


def _config(path) -> FakeConfig:
    return FakeConfig({("macie", "rulesbase"): str(path)})


def test_macie_project_rulesbase_directory() -> None:
    assert ProjectRulesbase.directory(config=None) is None
    assert ProjectRulesbase.directory(config=FakeConfig({})) == os.path.join(
        "rulesbase", "macie"
    )
    blank = FakeConfig({("macie", "rulesbase"): " "})
    assert ProjectRulesbase.directory(config=blank) == os.path.join(
        "rulesbase", "macie"
    )
    assert ProjectRulesbase.directory(config=_config("rb")) == os.path.join(
        "rb", "macie"
    )


def test_macie_project_rulesbase_absent_writes_nothing(tmp_path) -> None:
    #
    # no <rulesbase>/macie: the packaged catalog, and no new directories
    #
    base = tmp_path / "rulesbase"
    catalog = ProjectRulesbase.catalog(config=_config(base), refresh_reference=True)
    assert catalog.catalog == ManagedCatalog.load().catalog
    assert catalog.applied == []
    assert not base.exists()
    assert ProjectRulesbase.catalog(config=None).applied == []


def test_macie_project_rulesbase_reference_copy(tmp_path) -> None:
    d = tmp_path / "macie"
    d.mkdir()
    reference = d / ProjectRulesbase.REFERENCE
    #
    # a standalone run's read writes nothing; a load refreshes the copy
    #
    ProjectRulesbase.catalog(config=_config(tmp_path))
    assert not reference.exists()
    catalog = ProjectRulesbase.catalog(config=_config(tmp_path), refresh_reference=True)
    assert catalog.applied == []
    with open(ManagedCatalog.DEFAULT, encoding="utf-8") as f:
        assert reference.read_text(encoding="utf-8") == f.read()
    #
    # the reference copy is never read back: editing it changes nothing
    #
    reference.write_text("{ edited", encoding="utf-8")
    assert ProjectRulesbase.catalog(config=_config(tmp_path)).applied == []


def test_macie_project_rulesbase_overrides(tmp_path) -> None:
    d = tmp_path / "macie"
    d.mkdir()
    (d / ProjectRulesbase.OVERRIDES).write_text(
        json.dumps(
            {"version": 1, "keyword_lists": {"br_cep": {"keywords": ["código postal"]}}}
        ),
        encoding="utf-8",
    )
    catalog = ProjectRulesbase.catalog(config=_config(tmp_path), refresh_reference=True)
    assert catalog.applied == ["keyword_lists.br_cep"]
    assert catalog.overrides_path == str(d / ProjectRulesbase.OVERRIDES)
    assert catalog.identifier(name="BRAZIL_CEP_CODE")["keywords"] == ["código postal"]


def test_macie_project_rulesbase_bad_overrides_fail(tmp_path) -> None:
    d = tmp_path / "macie"
    d.mkdir()
    (d / ProjectRulesbase.OVERRIDES).write_text('{"version": 9}', encoding="utf-8")
    with pytest.raises(MacieException, match="version 9 is not supported"):
        ProjectRulesbase.catalog(config=_config(tmp_path))


def test_macie_project_rulesbase_bad_input() -> None:
    with pytest.raises(TypeError):
        ProjectRulesbase.catalog(config=None, refresh_reference="yes")


def test_macie_catalog_from_snapshot() -> None:
    snapshot = ManagedCatalog.load().catalog
    catalog = ManagedCatalog.from_snapshot(catalog=snapshot, where="group g")
    assert catalog.path == "group g"
    assert catalog.names == ManagedCatalog.load().names
    with pytest.raises(MacieException):
        ManagedCatalog.from_snapshot(catalog={"version": 1}, where="group g")
    with pytest.raises(ValueError):
        ManagedCatalog.from_snapshot(catalog=snapshot, where="")
