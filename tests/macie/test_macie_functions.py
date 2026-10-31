"""The Macie CVL functions through real runs, one behavior at a time. The
matching rules themselves are tested without CVL in
test_macie_custom_identifier and friends."""

import pytest

from csvpath import CsvPath
from csvpath.macie.functions.macie_run import MacieRun
from csvpath.util.printer import Printer

CDI = (
    'macie_cdi("EmployeeId", "", /EMP-\\d{6}/, "employee id", "", 50, '
    '"1:LOW 3:MEDIUM 5:HIGH"CAP)'
)


class StreamPrinter(Printer):
    __test__ = False

    def __init__(self) -> None:
        self.streams: dict[str, list[str]] = {}

    @property
    def lines_printed(self) -> int:
        return sum(len(v) for v in self.streams.values())

    @property
    def last_line(self) -> str:
        return ""

    def print(self, string: str) -> None:
        self.print_to("default", string)

    def print_to(self, name: str, string: str) -> None:
        self.streams.setdefault(name or "default", []).append(string)


def _csvpath(
    *,
    data: str,
    body: str,
    max_findings: int | None = 100,
    max_detail: int | None = 15,
    scan: str = "1*",
) -> str:
    metadata = [
        "id: test",
        "logic-mode: OR",
        "print-mode: separate",
        "validation-mode: collect, match, no-print, no-raise, no-fail, no-stop",
    ]
    if max_findings is not None:
        metadata.append(f"macie-max-findings: {max_findings}")
    if max_detail is not None:
        metadata.append(f"macie-max-detail: {max_detail}")
    md = "\n".join(f"  {m}" for m in metadata)
    return f"""~
{md}
~
${data}[{scan}][
    {body}
    last.nocontrib() -> macie_report()
]"""


def _write(tmp_path, *rows: str) -> str:
    p = tmp_path / "data.csv"
    text = "\n".join(["id,employee_id,notes", *rows]) + "\n"
    p.write_text(text, encoding="utf-8")
    return str(p)


def _run(text: str, *, config: dict | None = None):
    path = CsvPath()
    for (section, name), value in (config or {}).items():
        path.config.set(section=section, name=name, value=value)
    printer = StreamPrinter()
    path.set_printers([printer])
    matched = path.collect(text)
    return path, printer.streams.get("macie", []), [m[0] for m in matched]


def _cdi(cap: int | None = None) -> str:
    return CDI.replace("CAP", "" if cap is None else f", {cap}")


def test_macie_functions_two_occurrences_in_one_cell_are_both_reported(
    tmp_path,
) -> None:
    #
    # the error manager drops duplicate errors; occurrence numbers keep
    # these two distinct
    #
    data = _write(tmp_path, "1,EMP-111111 EMP-222222,")
    path, macie, matched = _run(_csvpath(data=data, body=_cdi()))
    assert matched == ["1"]
    assert [e.message for e in path.errors] == [
        "macie EmployeeId: occurrence 1, line 1 (row 2), column 2 employee_id",
        "macie EmployeeId: occurrence 2, line 1 (row 2), column 2 employee_id",
    ]
    assert macie[:2] == [e.message for e in path.errors]


def test_macie_functions_clean_lines_do_not_match(tmp_path) -> None:
    data = _write(tmp_path, "1,,nothing here", "2,EMP-111111,", "3,x,")
    path, macie, matched = _run(_csvpath(data=data, body=_cdi()))
    assert matched == ["2"]
    assert macie[-1] == (
        "macie EmployeeId: 1 occurrence, severity LOW, detail shown for all 1"
    )


def test_macie_functions_zero_findings(tmp_path) -> None:
    data = _write(tmp_path, "1,,", "2,x,")
    path, macie, matched = _run(_csvpath(data=data, body=_cdi()))
    assert matched == []
    assert path.errors == []
    assert macie == [
        "macie EmployeeId: 0 occurrences, severity none (below 1), no detail"
    ]
    findings = path.variables["macie_findings"]
    assert findings["customDataIdentifiers"] == {"detections": [], "totalCount": 0}
    assert findings["csvpath"]["stopped"] is False


def test_macie_functions_allow_list_order_does_not_matter(tmp_path) -> None:
    #
    # the allow list registers before any line is read, so it applies even
    # when it comes after the identifier in the csvpath
    #
    data = _write(tmp_path, "1,EMP-900001,", "2,EMP-111111,")
    body = f'{_cdi()}\n    macie_allow_regex.nocontrib("training", /EMP-9\\d{{5}}/)'
    path, macie, matched = _run(_csvpath(data=data, body=body))
    assert matched == ["2"]
    assert len(path.errors) == 1


def test_macie_functions_allow_list_never_matches_a_line(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-900001,", "2,x,")
    body = f'macie_allow_regex.nocontrib("training", /EMP-9\\d{{5}}/)\n    {_cdi()}'
    path, macie, matched = _run(_csvpath(data=data, body=body))
    assert matched == []


def test_macie_functions_detail_cap_keeps_counting(tmp_path) -> None:
    data = _write(tmp_path, *[f"{i},EMP-11111{i}," for i in range(1, 6)])
    path, macie, matched = _run(_csvpath(data=data, body=_cdi(), max_detail=2))
    assert matched == ["1", "2", "3", "4", "5"]
    assert len(path.errors) == 2
    assert macie[-1] == (
        "macie EmployeeId: 5 occurrences, severity HIGH, detail shown for first 2"
    )
    assert path.variables["macie_findings"]["customDataIdentifiers"]["totalCount"] == 5


def test_macie_functions_per_identifier_detail_cap(tmp_path) -> None:
    data = _write(tmp_path, *[f"{i},EMP-11111{i}," for i in range(1, 6)])
    path, macie, matched = _run(_csvpath(data=data, body=_cdi(cap=1), max_detail=4))
    assert len(path.errors) == 1
    assert macie[-1].endswith("detail shown for first 1")


def test_macie_functions_breaker_stops_and_reports(tmp_path) -> None:
    data = _write(tmp_path, *[f"{i},EMP-11111{i}," for i in range(1, 8)])
    path, macie, matched = _run(_csvpath(data=data, body=_cdi(), max_findings=3))
    #
    # stop() ends the run on the line that reaches the max; that line isn't
    # matched because the matcher returns as soon as it sees the stop
    #
    assert matched == ["1", "2"]
    assert path.stopped is True
    assert macie[-2:] == [
        "macie EmployeeId: 3 occurrences, severity MEDIUM, detail shown for all 3",
        "macie: stopped at line 3 after 3 occurrences (max 3); results are "
        "partial and severities are at least as shown",
    ]
    #
    # reported once, even though nothing more ran
    #
    assert len([m for m in macie if "occurrences, severity" in m]) == 1
    csvpath = path.variables["macie_findings"]["csvpath"]
    assert csvpath == {
        "source_arn": None,
        "stopped": True,
        "stopped_at_line": 3,
        "max_findings": 3,
        "max_detail": 15,
    }


def test_macie_functions_breaker_mid_cell(tmp_path) -> None:
    #
    # the breaker trips between two occurrences in one cell: the second
    # is not recorded
    #
    data = _write(tmp_path, "1,EMP-111111,", "2,EMP-222222 EMP-333333,")
    path, macie, matched = _run(_csvpath(data=data, body=_cdi(), max_findings=2))
    findings = path.variables["macie_findings"]
    assert findings["customDataIdentifiers"]["totalCount"] == 2
    assert len(path.errors) == 2


def test_macie_functions_header_only_file(tmp_path) -> None:
    #
    # no data line is scanned. last() fires on the final, frozen pass and
    # lifts the variable freeze for macie_report()
    #
    data = _write(tmp_path)
    path, macie, matched = _run(_csvpath(data=data, body=_cdi()))
    assert matched == []
    assert macie == [
        "macie EmployeeId: 0 occurrences, severity none (below 1), no detail"
    ]
    assert path.variables["macie_findings"]["customDataIdentifiers"]["totalCount"] == 0


def test_macie_functions_trailing_blank_lines(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,", "2,x,")
    with open(data, "a", encoding="utf-8") as f:
        f.write("\n\n")
    path, macie, matched = _run(_csvpath(data=data, body=_cdi()))
    assert matched == ["1"]
    assert path.variables["macie_findings"]["customDataIdentifiers"]["totalCount"] == 1
    assert len([m for m in macie if "occurrence, severity" in m]) == 1


def test_macie_functions_last_line_outside_scan_range(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,", "2,x,", "3,EMP-222222,")
    path, macie, matched = _run(_csvpath(data=data, body=_cdi(), scan="1-2"))
    assert matched == ["1"]
    assert path.variables["macie_findings"]["customDataIdentifiers"]["totalCount"] == 1
    assert macie[-1] == (
        "macie EmployeeId: 1 occurrence, severity LOW, detail shown for all 1"
    )


def test_macie_functions_limits_from_config(tmp_path) -> None:
    data = _write(tmp_path, *[f"{i},EMP-11111{i}," for i in range(1, 6)])
    text = _csvpath(data=data, body=_cdi(), max_findings=None, max_detail=None)
    path, macie, matched = _run(
        text, config={("macie", "max_findings"): "4", ("macie", "max_detail"): "1"}
    )
    assert path.variables["macie_findings"]["csvpath"]["max_findings"] == 4
    assert path.variables["macie_findings"]["csvpath"]["max_detail"] == 1
    assert len(path.errors) == 1


def test_macie_functions_metadata_beats_config(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    text = _csvpath(data=data, body=_cdi(), max_findings=7, max_detail=2)
    path, macie, matched = _run(text, config={("macie", "max_findings"): "4"})
    assert path.variables["macie_findings"]["csvpath"]["max_findings"] == 7


def test_macie_functions_default_limits(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    text = _csvpath(data=data, body=_cdi(), max_findings=None, max_detail=None)
    path, macie, matched = _run(text)
    csvpath = path.variables["macie_findings"]["csvpath"]
    assert csvpath["max_findings"] == MacieRun.MAX_FINDINGS
    assert csvpath["max_detail"] == MacieRun.MAX_DETAIL


def _assert_cannot_run(path, macie: list[str], matched: list, message: str) -> None:
    #
    # with no-raise the error is only recorded. the run must still not look
    # like a clean file.
    #
    assert matched == []
    assert path.is_valid is False
    assert path.stopped is True
    assert macie == [f"macie: cannot run: {message}"]
    assert message in [e.message for e in path.errors]


@pytest.mark.parametrize(
    "value, message",
    [
        ("lots", "metadata macie-max-findings must be an int, not 'lots'"),
        ("0", "metadata macie-max-findings must be at least 1, not 0"),
        ("-1", "metadata macie-max-findings must be at least 1, not -1"),
    ],
)
def test_macie_functions_bad_max_findings(tmp_path, value: str, message: str) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    text = _csvpath(data=data, body=_cdi(), max_findings=None).replace(
        "  id: test", f"  id: test\n  macie-max-findings: {value}"
    )
    _assert_cannot_run(*_run(text), message)


def test_macie_functions_bad_regex_cannot_run(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    body = 'macie_cdi("X", "", /(?=EMP/, "", "", 50, "1:LOW")'
    _assert_cannot_run(
        *_run(_csvpath(data=data, body=body)),
        "Unclosed ( at position 0 in Macie regex '(?=EMP'",
    )


def test_macie_functions_bad_allow_list_cannot_run(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    body = f'macie_allow_regex.nocontrib("a", /(EMP/)\n    {_cdi()}'
    path, macie, matched = _run(_csvpath(data=data, body=body))
    assert path.is_valid is False
    assert path.stopped is True
    assert macie[0].startswith("macie: cannot run: ")


def test_macie_functions_bad_input_raises_in_raise_mode(tmp_path) -> None:
    from csvpath.macie.macie_exceptions import MacieException

    data = _write(tmp_path, "1,EMP-111111,")
    body = 'macie_cdi("X", "", /(?=EMP/, "", "", 50, "1:LOW")'
    text = _csvpath(data=data, body=body).replace("no-raise", "raise")
    with pytest.raises(MacieException):
        CsvPath().collect(text)


CDI_ARN = "arn:aws:macie2:us-east-1:123456789012:custom-data-identifier/2a1b"
JOB_ARN = "arn:aws:macie2:us-east-1:123456789012:classification-job/5d0c"


def test_macie_functions_arns_reach_the_findings(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    body = _cdi().replace('"EmployeeId", ""', f'"EmployeeId", "{CDI_ARN}"')
    text = _csvpath(data=data, body=body).replace(
        "  id: test", f"  id: test\n  macie-source-arn: {JOB_ARN.replace(':', '|')}"
    )
    path, macie, matched = _run(text)
    findings = path.variables["macie_findings"]
    assert findings["customDataIdentifiers"]["detections"][0]["arn"] == CDI_ARN
    assert findings["csvpath"]["source_arn"] == JOB_ARN


def test_macie_functions_no_arns(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    path, macie, matched = _run(_csvpath(data=data, body=_cdi()))
    findings = path.variables["macie_findings"]
    assert findings["customDataIdentifiers"]["detections"][0]["arn"] is None
    assert findings["csvpath"]["source_arn"] is None


def test_macie_functions_bad_cdi_arn_cannot_run(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    body = _cdi().replace('"EmployeeId", ""', '"EmployeeId", "arn:aws:s3:::bucket"')
    _assert_cannot_run(
        *_run(_csvpath(data=data, body=body)),
        "Not a Macie ARN: 'arn:aws:s3:::bucket'",
    )


def test_macie_functions_bad_source_arn_cannot_run(tmp_path) -> None:
    data = _write(tmp_path, "1,EMP-111111,")
    text = _csvpath(data=data, body=_cdi()).replace(
        "  id: test", "  id: test\n  macie-source-arn: arn|aws|s3|||bucket"
    )
    _assert_cannot_run(*_run(text), "Not a Macie ARN: 'arn:aws:s3:::bucket'")
