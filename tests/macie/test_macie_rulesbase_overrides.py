"""A project rulesbase's overrides merged over the packaged catalog
(RulesbaseOverrides, ManagedCatalog.load(overrides_path=...)):
specs/macie/rulesbase-design.md, P1. The examples are the design's."""

import json

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors import DETECTORS
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.rulesbase_overrides import RulesbaseOverrides
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
#
# documentation keys in the packaged detector entries, read by no detector
#
DOC_KEYS = {"notes", "exclusions_source"}


@pytest.fixture
def write(tmp_path):
    def _write(overrides) -> str:
        p = tmp_path / "managed_identifiers.json"
        p.write_text(json.dumps(overrides), encoding="utf-8")
        return str(p)

    return _write


def _mdi(catalog: ManagedCatalog, name: str) -> ManagedIdentifier:
    e = catalog.identifier(name=name)
    return ManagedIdentifier(
        name=name,
        category=e["category"],
        detector=e["detector"],
        keyword_mode=e["keyword_mode"],
        keywords=e["keywords"],
        distance=e["distance"],
        severity=SeverityLevels.parse(text=e["severity"]),
        catalog=catalog,
    )


def test_macie_config_keys_cover_the_packaged_detectors() -> None:
    #
    # every key a packaged detector entry has is one its class reads (or
    # documentation), so the overridable keys are the real ones; a key added
    # to the catalog without CONFIG_KEYS fails here
    #
    catalog = ManagedCatalog.load()
    for name, entry in catalog.catalog["detectors"].items():
        keys = set(DETECTORS[name].CONFIG_KEYS)
        assert set(entry) - DOC_KEYS <= keys, name


def test_macie_no_overrides_is_the_packaged_catalog() -> None:
    catalog = ManagedCatalog.load()
    assert catalog.applied == []
    assert catalog.overrides_path is None


def test_macie_override_keyword_list(write) -> None:
    #
    # design example 1: rg matches a cargo column, so keep only the long
    # keyword
    #
    path = write(
        {
            "version": 1,
            "keyword_lists": {
                "br_rg": {"keywords": ["registro geral"], "why": "rg matches cargo"}
            },
        }
    )
    catalog = ManagedCatalog.load(overrides_path=path)
    assert catalog.applied == ["keyword_lists.br_rg"]
    assert catalog.overrides_path == path
    e = catalog.identifier(name="BRAZIL_RG_NUMBER")
    assert e["keywords"] == ["registro geral"]
    #
    # the packaged fields not named stay, and the why is kept
    #
    kl = catalog.catalog["keyword_lists"]["br_rg"]
    assert kl["why"] == "rg matches cargo"
    assert kl["source"].startswith("https://docs.aws.amazon.com/macie/")
    rg = _mdi(catalog, "BRAZIL_RG_NUMBER")
    assert (
        rg.occurrences(cell="12.345.678-9", header="cargo", allow_lists=NO_ALLOW) == 0
    )
    assert (
        rg.occurrences(
            cell="registro geral 12.345.678-9", header="x", allow_lists=NO_ALLOW
        )
        == 1
    )


def test_macie_override_identifier_keys_only(write) -> None:
    #
    # design example 2: only the named key changes
    #
    path = write(
        {
            "version": 1,
            "identifiers": {"LATITUDE_LONGITUDE": {"severity": "1:MEDIUM 2:HIGH"}},
        }
    )
    catalog = ManagedCatalog.load(overrides_path=path)
    packaged = ManagedCatalog.load().identifier(name="LATITUDE_LONGITUDE")
    e = catalog.identifier(name="LATITUDE_LONGITUDE")
    assert e["severity"] == "1:MEDIUM 2:HIGH"
    assert {k: v for k, v in e.items() if k != "severity"} == {
        k: v for k, v in packaged.items() if k != "severity"
    }


def test_macie_override_detector_formats(write) -> None:
    #
    # design example 3: Minas Gerais RG numbers
    #
    path = write(
        {
            "version": 1,
            "detectors": {
                "br_rg": {
                    "formats": [
                        "##.###.###-[0-9X]",
                        "#{8}-[0-9X]",
                        "#{8}[0-9X]",
                        "[M][G]-##.###.###",
                    ]
                }
            },
        }
    )
    catalog = ManagedCatalog.load(overrides_path=path)
    rg = _mdi(catalog, "BRAZIL_RG_NUMBER")
    assert (
        rg.occurrences(cell="RG MG-12.345.678", header="x", allow_lists=NO_ALLOW) == 1
    )
    packaged = _mdi(ManagedCatalog.load(), "BRAZIL_RG_NUMBER")
    assert (
        packaged.occurrences(cell="RG MG-12.345.678", header="x", allow_lists=NO_ALLOW)
        == 0
    )
    assert catalog.catalog["detectors"]["br_rg"]["notes"]


def test_macie_override_new_keyword_list(write) -> None:
    #
    # a new list, for one identifier that shares a list with others
    #
    path = write(
        {
            "version": 1,
            "keyword_lists": {"our_dl": {"keywords": ["licence no"]}},
            "identifiers": {"UK_DRIVERS_LICENSE": {"keywords_from": "our_dl"}},
        }
    )
    catalog = ManagedCatalog.load(overrides_path=path)
    assert catalog.applied == [
        "keyword_lists.our_dl",
        "identifiers.UK_DRIVERS_LICENSE",
    ]
    assert catalog.identifier(name="UK_DRIVERS_LICENSE")["keywords"] == ["licence no"]


def test_macie_merge_does_not_change_the_base() -> None:
    base = ManagedCatalog.load().catalog
    before = json.dumps(base, sort_keys=True)
    merged, applied = RulesbaseOverrides.merge(
        base=base,
        overrides={"version": 1, "keyword_lists": {"br_rg": {"keywords": ["x y"]}}},
        path="p.json",
    )
    assert applied == ["keyword_lists.br_rg"]
    assert merged["keyword_lists"]["br_rg"]["keywords"] == ["x y"]
    assert json.dumps(base, sort_keys=True) == before


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"version": 2}, "version 2 is not supported"),
        ({}, "version None is not supported"),
        ({"version": 1, "identifier": {}}, "unknown sections: identifier"),
        ({"version": 1, "identifiers": []}, "identifiers must be an object"),
        (
            {"version": 1, "identifiers": {"NOPE": {"severity": "1:HIGH"}}},
            "not in the packaged",
        ),
        (
            {"version": 1, "detectors": {"nope": {"formats": ["#"]}}},
            "not in the packaged",
        ),
        ({"version": 1, "identifiers": {"LATITUDE_LONGITUDE": {}}}, "non-empty object"),
        (
            {"version": 1, "identifiers": {"LATITUDE_LONGITUDE": {"category": "X"}}},
            "cannot override category",
        ),
        (
            {"version": 1, "identifiers": {"LATITUDE_LONGITUDE": {"detector": "vin"}}},
            "cannot override detector",
        ),
        (
            {"version": 1, "detectors": {"br_rg": {"formts": ["#"]}}},
            "cannot override formts",
        ),
        (
            {"version": 1, "keyword_lists": {"br_rg": {"source": "x"}}},
            "cannot override source",
        ),
        (
            {"version": 1, "keyword_lists": {"br_rg": {"keywords": ["rg"], "why": ""}}},
            "why must be a non-empty str",
        ),
        #
        # caught by the merged catalog's validation
        #
        (
            {"version": 1, "identifiers": {"LATITUDE_LONGITUDE": {"severity": "lots"}}},
            "severity",
        ),
        (
            {
                "version": 1,
                "identifiers": {"BRAZIL_RG_NUMBER": {"keywords_from": "nope"}},
            },
            "names keyword list 'nope'",
        ),
        ({"version": 1, "keyword_lists": {"new": {"why": "x"}}}, "needs keywords"),
        (
            {"version": 1, "keyword_lists": {"br_rg": {"keywords": ['a "b"']}}},
            "Bad keyword",
        ),
        #
        # caught by building the detector
        #
        (
            {"version": 1, "detectors": {"br_rg": {"formats": ["Q#"]}}},
            "must be in a set",
        ),
        (
            {"version": 1, "detectors": {"iban": {"lengths": "x"}}},
            "ALBANIA_BANK_ACCOUNT",
        ),
    ],
)
def test_macie_bad_overrides_fail_loudly(write, overrides, message) -> None:
    with pytest.raises(MacieException, match=message):
        ManagedCatalog.load(overrides_path=write(overrides))


def test_macie_overrides_file_problems(tmp_path) -> None:
    with pytest.raises(MacieException, match="Cannot read project rulesbase"):
        ManagedCatalog.load(overrides_path=str(tmp_path / "missing.json"))
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(MacieException, match="Cannot read project rulesbase"):
        ManagedCatalog.load(overrides_path=str(bad))
    listed = tmp_path / "list.json"
    listed.write_text("[]", encoding="utf-8")
    with pytest.raises(MacieException, match="must be a JSON object"):
        ManagedCatalog.load(overrides_path=str(listed))


def test_macie_overrides_bad_arguments() -> None:
    with pytest.raises(ValueError):
        ManagedCatalog.load(overrides_path="")
    with pytest.raises(ValueError):
        RulesbaseOverrides.read(path=" ")
    with pytest.raises(TypeError):
        RulesbaseOverrides.merge(base=None, overrides={"version": 1}, path="p")
    with pytest.raises(ValueError):
        RulesbaseOverrides.merge(base={}, overrides={"version": 1}, path="")
