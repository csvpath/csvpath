import copy
import json
import os

import pytest

from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.macie_exceptions import MacieException

RESOURCES = os.path.join("tests", "macie", "test_resources")
JOB_DOWNLOAD = os.path.join(RESOURCES, "wrappers", "job_download.macie.json")
HANDCRAFTED = os.path.join(RESOURCES, "wrappers", "handcrafted_minimal.macie.json")
PAIR_01 = os.path.join(
    RESOURCES, "normative", "01_employee_ids", "hr-employee-ids.macie.json"
)


def _minimal() -> dict:
    return {
        "csvpath_macie": 1,
        "source": {"origin": "handcrafted"},
        "selection": {
            "managedDataIdentifierSelector": "NONE",
            "customDataIdentifierIds": ["c1"],
            "allowListIds": [],
        },
        "managedDataIdentifiers": {"resolved": []},
        "customDataIdentifiers": [{"id": "c1", "name": "C1", "regex": "X\\d+"}],
    }


def _text_allow_list(*, status: str = "OK", entries: list = None) -> dict:
    return {
        "settings": {
            "id": "a1",
            "name": "names",
            "criteria": {"s3WordsList": {"bucketName": "b1x", "objectKey": "k.txt"}},
        },
        "contents": {
            "status": status,
            "entries": ["Akua Mansa"] if entries is None else entries,
            "sha256": "0" * 64 if status == "OK" else None,
            "error": None,
        },
    }


def _with_allow_list(allow_list: dict) -> dict:
    w = _minimal()
    w["selection"]["allowListIds"] = [allow_list["settings"]["id"]]
    w["allowLists"] = [allow_list]
    return w


def _fails(wrapper: dict, match: str) -> None:
    with pytest.raises(MacieException, match=match):
        MacieWrapperLoader.validate(wrapper=wrapper)


#
# file and text entry points
#


def test_macie_loader_has_a_schema_file_for_every_version() -> None:
    for version in MacieWrapperLoader.SCHEMAS:
        schema = MacieWrapperLoader.schema(version=version)
        assert schema["properties"]["csvpath_macie"]["const"] == version
    with pytest.raises(ValueError):
        MacieWrapperLoader.schema(version=99)


def test_macie_loader_is_wrapper_path() -> None:
    assert MacieWrapperLoader.is_wrapper_path(path="a/b/hr.macie.json")
    assert not MacieWrapperLoader.is_wrapper_path(path="a/b/hr.json")
    assert not MacieWrapperLoader.is_wrapper_path(path="hr.macie.json.bak")
    with pytest.raises(TypeError):
        MacieWrapperLoader.is_wrapper_path(path=None)


@pytest.mark.parametrize("path", [JOB_DOWNLOAD, HANDCRAFTED, PAIR_01])
def test_macie_loader_example_wrappers_are_valid(path: str) -> None:
    wrapper = MacieWrapperLoader.from_path(path=path)
    assert wrapper["csvpath_macie"] == 1


def test_macie_loader_from_path_bad_input() -> None:
    with pytest.raises(ValueError):
        MacieWrapperLoader.from_path(path="")
    with pytest.raises(ValueError):
        MacieWrapperLoader.from_path(path=None)
    with pytest.raises(ValueError, match="must end in"):
        MacieWrapperLoader.from_path(path=os.path.join(RESOURCES, "hr.json"))
    with pytest.raises(ValueError, match="No Macie wrapper"):
        MacieWrapperLoader.from_path(path="no/such/hr.macie.json")


def test_macie_loader_from_string() -> None:
    wrapper = MacieWrapperLoader.from_string(text=json.dumps(_minimal()))
    assert wrapper == _minimal()


def test_macie_loader_from_string_bad_input() -> None:
    with pytest.raises(ValueError):
        MacieWrapperLoader.from_string(text="  ")
    with pytest.raises(TypeError):
        MacieWrapperLoader.from_string(text=None)
    with pytest.raises(MacieException, match="Cannot parse"):
        MacieWrapperLoader.from_string(text='{"csvpath_macie": ')
    with pytest.raises(TypeError):
        MacieWrapperLoader.from_string(text="[1, 2]")


#
# marker, version, and schema
#


def test_macie_loader_minimal_is_valid() -> None:
    assert MacieWrapperLoader.validate(wrapper=_minimal()) == _minimal()


def test_macie_loader_validate_bad_input() -> None:
    with pytest.raises(TypeError):
        MacieWrapperLoader.validate(wrapper=None)
    with pytest.raises(TypeError):
        MacieWrapperLoader.validate(wrapper=[])


def test_macie_loader_needs_marker() -> None:
    w = _minimal()
    del w["csvpath_macie"]
    _fails(w, "Not a Macie wrapper")


@pytest.mark.parametrize("version", [2, "1", True, 0])
def test_macie_loader_unsupported_version(version) -> None:
    w = _minimal()
    w["csvpath_macie"] = version
    _fails(w, "Unsupported Macie wrapper version")


def test_macie_loader_does_not_change_its_input() -> None:
    w = _minimal()
    before = copy.deepcopy(w)
    MacieWrapperLoader.validate(wrapper=w)
    assert w == before


@pytest.mark.parametrize("key", ["source", "selection", "managedDataIdentifiers"])
def test_macie_loader_required_top_level_keys(key: str) -> None:
    w = _minimal()
    del w[key]
    _fails(w, "is a required property")


def test_macie_loader_unknown_top_level_key() -> None:
    w = _minimal()
    w["customDataIdentifers"] = []
    _fails(w, "Additional properties")


def test_macie_loader_downloaded_by_is_not_part_of_the_format() -> None:
    w = MacieWrapperLoader.from_path(path=JOB_DOWNLOAD)
    w["source"]["downloaded_by"] = "arn:aws:iam::123456789012:user/x"
    _fails(w, "Additional properties")


@pytest.mark.parametrize(
    "origin, needs",
    [("job", "job_id"), ("template", "template_id")],
)
def test_macie_loader_downloaded_origins_need_their_fields(origin, needs) -> None:
    w = _minimal()
    w["source"] = {"origin": origin}
    _fails(w, "is a required property")
    for field in [needs, "account_id", "region", "downloaded_at"]:
        w["source"] = {
            "origin": origin,
            "job_id": "j",
            "template_id": "t",
            "account_id": "123456789012",
            "region": "us-east-1",
            "downloaded_at": "2026-10-29T17:40:00Z",
        }
        del w["source"][field]
        _fails(w, f"'{field}' is a required property")


def test_macie_loader_downloaded_at_format() -> None:
    w = MacieWrapperLoader.from_path(path=JOB_DOWNLOAD)
    w["source"]["downloaded_at"] = "2026-10-29 17:40:00"
    _fails(w, "downloaded_at")


def test_macie_loader_bad_selector() -> None:
    w = _minimal()
    w["selection"]["managedDataIdentifierSelector"] = "SOME"
    _fails(w, "managedDataIdentifierSelector")


def test_macie_loader_custom_identifier_needs_a_regex() -> None:
    w = _minimal()
    w["customDataIdentifiers"][0]["regex"] = ""
    _fails(w, "regex")
    del w["customDataIdentifiers"][0]["regex"]
    _fails(w, "'regex' is a required property")


def test_macie_loader_custom_identifier_macie_limits() -> None:
    w = _minimal()
    w["customDataIdentifiers"][0]["keywords"] = ["ab"]
    _fails(w, "keywords")
    w = _minimal()
    w["customDataIdentifiers"][0]["maximumMatchDistance"] = 301
    _fails(w, "maximumMatchDistance")
    w = _minimal()
    w["customDataIdentifiers"][0]["severityLevels"] = [
        {"occurrencesThreshold": 1, "severity": "URGENT"}
    ]
    _fails(w, "severity")


def test_macie_loader_custom_identifier_keeps_unknown_aws_fields() -> None:
    #
    # verbatim AWS responses may grow new fields; they must not be rejected
    #
    w = _minimal()
    w["customDataIdentifiers"][0]["someNewAwsField"] = {"x": 1}
    MacieWrapperLoader.validate(wrapper=w)


def test_macie_loader_allow_list_criteria_is_one_kind() -> None:
    a = _text_allow_list()
    a["settings"]["criteria"]["regex"] = "X"
    _fails(_with_allow_list(a), "criteria")
    a["settings"]["criteria"] = {}
    _fails(_with_allow_list(a), "criteria")


def test_macie_loader_unknown_warning_code() -> None:
    w = _minimal()
    w["warnings"] = [{"code": "SOMETHING", "message": "m"}]
    _fails(w, "code")


#
# cross-checks the schema can't express
#


def test_macie_loader_template_selector_must_be_recommended() -> None:
    w = _minimal()
    w["source"] = {
        "origin": "template",
        "template_id": "t",
        "account_id": "123456789012",
        "region": "us-east-1",
        "downloaded_at": "2026-10-29T17:40:00Z",
    }
    _fails(w, "must use selector RECOMMENDED")


def test_macie_loader_selected_and_entries_match_one_to_one() -> None:
    w = _minimal()
    w["selection"]["customDataIdentifierIds"] = ["c1", "c2"]
    _fails(w, "Selected in customDataIdentifierIds but not in customDataIdentifiers")
    w = _minimal()
    w["selection"]["customDataIdentifierIds"] = []
    _fails(w, "In customDataIdentifiers but not selected")
    w = _with_allow_list(_text_allow_list())
    w["selection"]["allowListIds"] = []
    _fails(w, "In allowLists but not selected")


def test_macie_loader_no_duplicate_ids() -> None:
    w = _minimal()
    w["customDataIdentifiers"].append({"id": "c1", "name": "again", "regex": "Y"})
    _fails(w, "Duplicate ids in customDataIdentifiers")
    w = _minimal()
    w["selection"]["customDataIdentifierIds"] = ["c1", "c1"]
    _fails(w, "Duplicate ids in selection.customDataIdentifierIds")
    w = _minimal()
    w["selection"]["managedDataIdentifierSelector"] = "ALL"
    w["managedDataIdentifiers"]["resolved"] = ["NAME", "NAME"]
    _fails(w, "Duplicate ids in managedDataIdentifiers.resolved")


def _selector(
    selector: str, *, included=None, excluded=None, resolved=None, rec=None
) -> dict:
    w = _minimal()
    w["selection"]["managedDataIdentifierSelector"] = selector
    w["selection"]["managedDataIdentifierIds"] = included or []
    w["selection"]["excludedManagedDataIdentifierIds"] = excluded or []
    w["managedDataIdentifiers"]["resolved"] = resolved or []
    w["managedDataIdentifiers"]["resolution"] = {
        "method": "selector",
        "recommended_list": rec,
    }
    return w


def test_macie_loader_selector_none() -> None:
    MacieWrapperLoader.validate(wrapper=_selector("NONE"))
    _fails(_selector("NONE", resolved=["NAME"]), "Selector NONE")
    _fails(_selector("NONE", included=["NAME"]), "Selector NONE")


def test_macie_loader_selector_include() -> None:
    MacieWrapperLoader.validate(
        wrapper=_selector(
            "INCLUDE", included=["NAME", "PKCS"], resolved=["PKCS", "NAME"]
        )
    )
    _fails(_selector("INCLUDE"), "INCLUDE needs managedDataIdentifierIds")
    _fails(
        _selector("INCLUDE", included=["NAME"], resolved=["NAME", "PKCS"]),
        "resolved must be exactly",
    )
    _fails(
        _selector("INCLUDE", included=["NAME"], resolved=["NAME"], excluded=["PKCS"]),
        "cannot have excluded",
    )


def test_macie_loader_selector_exclude() -> None:
    MacieWrapperLoader.validate(
        wrapper=_selector("EXCLUDE", excluded=["NAME"], resolved=["PKCS"])
    )
    _fails(_selector("EXCLUDE", resolved=["PKCS"]), "EXCLUDE needs")
    _fails(
        _selector("EXCLUDE", excluded=["NAME"], resolved=["NAME", "PKCS"]),
        "Excluded managed data identifiers are resolved",
    )
    _fails(
        _selector("EXCLUDE", excluded=["NAME"], included=["PKCS"], resolved=["PKCS"]),
        "cannot have managedDataIdentifierIds",
    )


def test_macie_loader_selector_all() -> None:
    MacieWrapperLoader.validate(wrapper=_selector("ALL", resolved=["NAME", "PKCS"]))
    _fails(_selector("ALL", included=["NAME"], resolved=["NAME"]), "Selector ALL")


def test_macie_loader_selector_recommended() -> None:
    rec = "jobs-recommended@2026-10-29"
    MacieWrapperLoader.validate(
        wrapper=_selector("RECOMMENDED", resolved=["PKCS"], rec=rec)
    )
    MacieWrapperLoader.validate(
        wrapper=_selector(
            "RECOMMENDED",
            included=["NAME"],
            excluded=["AWS_CREDENTIALS"],
            resolved=["PKCS", "NAME"],
            rec=rec,
        )
    )
    _fails(
        _selector("RECOMMENDED", resolved=["PKCS"]), "needs resolution.recommended_list"
    )
    _fails(
        _selector("RECOMMENDED", included=["NAME"], resolved=["PKCS"], rec=rec),
        "Included managed data identifiers not resolved",
    )


def test_macie_loader_only_recommended_names_a_recommended_list() -> None:
    _fails(
        _selector("ALL", resolved=["PKCS"], rec="jobs-recommended@2026-10-29"),
        "Selector ALL cannot have resolution.recommended_list",
    )


def test_macie_loader_text_allow_list_contents() -> None:
    MacieWrapperLoader.validate(wrapper=_with_allow_list(_text_allow_list()))
    MacieWrapperLoader.validate(
        wrapper=_with_allow_list(_text_allow_list(status="ACCESS_DENIED", entries=[]))
    )
    a = _text_allow_list()
    del a["contents"]
    _fails(_with_allow_list(a), "has no contents")
    _fails(_with_allow_list(_text_allow_list(entries=[])), "status OK but no entries")
    a = _text_allow_list()
    a["contents"]["sha256"] = None
    _fails(_with_allow_list(a), "status OK but no sha256")
    _fails(
        _with_allow_list(_text_allow_list(status="NOT_FOUND", entries=["x"])),
        "has status NOT_FOUND but has entries",
    )


def test_macie_loader_regex_allow_list_has_no_contents() -> None:
    a = _text_allow_list()
    a["settings"]["criteria"] = {"regex": "EMP-9\\d{5}"}
    _fails(_with_allow_list(a), "Regex allow list names cannot have contents")
    del a["contents"]
    MacieWrapperLoader.validate(wrapper=_with_allow_list(a))
