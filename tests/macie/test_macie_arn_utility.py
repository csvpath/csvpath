import pytest

from csvpath import CsvPath
from csvpath.macie.arn_utility import ArnUtility as arut
from csvpath.macie.macie_exceptions import MacieException

JOB = "arn:aws:macie2:us-east-1:123456789012:classification-job/5d0c4a1e8b7f"
GOV = (
    "arn:aws-us-gov:macie2:us-gov-west-1:123456789012:custom-data-identifier/2a1b-7e4c"
)


@pytest.mark.parametrize("arn", [JOB, GOV])
def test_macie_arn_round_trip(arn: str) -> None:
    value = arut.to_metadata(arn=arn)
    assert ":" not in value
    assert arut.from_metadata(value=value) == arn


def test_macie_arn_to_metadata() -> None:
    assert arut.to_metadata(arn=JOB) == (
        "arn|aws|macie2|us-east-1|123456789012|classification-job/5d0c4a1e8b7f"
    )


def test_macie_arn_survives_the_metadata_parser(tmp_path) -> None:
    #
    # the reason for the swap: a ":" in a value would start new keys
    #
    data = tmp_path / "d.csv"
    data.write_text("a\n1\n", encoding="utf-8")
    path = CsvPath()
    path.collect(
        f"""~
  id: probe
  macie-source-arn: {arut.to_metadata(arn=GOV)}
~
${data}[1*][ yes() ]"""
    )
    assert arut.from_metadata(value=path.metadata["macie-source-arn"]) == GOV


@pytest.mark.parametrize(
    "arn",
    [
        "",
        "arn:aws:s3:::bucket",
        "arn:aws:macie2:us-east-1:1234:classification-job/x",
        "arn|aws|macie2|us-east-1|123456789012|classification-job/x",
        f"{JOB} ",
        f"{JOB}|x",
    ],
)
def test_macie_arn_check_rejects(arn: str) -> None:
    with pytest.raises(MacieException):
        arut.check(arn=arn)
    with pytest.raises(MacieException):
        arut.to_metadata(arn=arn)


def test_macie_arn_from_metadata_rejects_colons() -> None:
    with pytest.raises(MacieException):
        arut.from_metadata(value=JOB)


def test_macie_arn_bad_input() -> None:
    with pytest.raises(TypeError):
        arut.check(arn=None)
    with pytest.raises(TypeError):
        arut.from_metadata(value=None)
