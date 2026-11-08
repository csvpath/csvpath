"""The recommended managed identifier sets, shipped as dated assets
(RecommendedLists; specs/macie/download-design.md)."""

import datetime

import pytest

from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.recommended_lists import RecommendedLists

UTC = datetime.timezone.utc
#
# Macie identifiers we have no stand-in for. A recommended id outside the
# catalog must be one of these, so a new gap fails here rather than in a
# customer's conversion report. SPAIN_SOCIAL_SECURITY_NUMBER was found
# missing from our inventory on 2026-11-08: worklist, next stand-in.
#
NO_STAND_IN = {
    "NAME",
    "ADDRESS",
    "SPAIN_SOCIAL_SECURITY_NUMBER",
} | {
    f"{c}_DRIVERS_LICENSE"
    for c in (
        "FINLAND GREECE HUNGARY IRELAND LATVIA LITHUANIA LUXEMBOURG MALTA "
        "NETHERLANDS POLAND PORTUGAL ROMANIA SLOVAKIA SLOVENIA SWEDEN"
    ).split()
}


@pytest.mark.parametrize("name", RecommendedLists.NAMES)
def test_macie_recommended_list_loads(name: str) -> None:
    data = RecommendedLists.load(name=name)
    assert data["source"].startswith("https://docs.aws.amazon.com/macie/")
    assert data["retrieved"] == "2026-11-08"
    catalog = ManagedCatalog.load()
    assert set(data["ids"]) - set(catalog.names) <= NO_STAND_IN


def test_macie_recommended_list_sizes() -> None:
    #
    # as published, retrieved 2026-11-08: the jobs set and the dynamic
    # automated discovery set are the same 35; the static set is 100
    #
    jobs = RecommendedLists.load(name=RecommendedLists.JOBS)["ids"]
    dynamic = RecommendedLists.load(name=RecommendedLists.AUTOMATED)["ids"]
    static = RecommendedLists.load(name=RecommendedLists.AUTOMATED_STATIC)["ids"]
    assert len(jobs) == 35
    assert set(dynamic) == set(jobs)
    assert len(static) == 100
    assert set(jobs) <= set(static)
    assert "CREDIT_CARD_NUMBER" in jobs
    assert "CREDIT_CARD_NUMBER_(NO_KEYWORD)" not in jobs
    assert {"NAME", "ADDRESS"} <= set(static)


def test_macie_recommended_for_job() -> None:
    ids, label = RecommendedLists.for_job()
    assert label == "jobs-recommended@2026-11-08"
    assert len(ids) == 35


@pytest.mark.parametrize(
    "when, label",
    [
        (datetime.datetime(2023, 8, 2, tzinfo=UTC), "automated-discovery-recommended"),
        (datetime.datetime(2025, 1, 1, tzinfo=UTC), "automated-discovery-recommended"),
        (
            datetime.datetime(2023, 8, 1, 23, 59, tzinfo=UTC),
            "automated-discovery-static",
        ),
        (datetime.datetime(2022, 11, 28, tzinfo=UTC), "automated-discovery-static"),
    ],
)
def test_macie_recommended_for_template(when, label: str) -> None:
    ids, got = RecommendedLists.for_template(first_enabled_at=when)
    assert got == f"{label}@2026-11-08"
    assert len(ids) == (35 if label.endswith("recommended") else 100)


def test_macie_recommended_bad_input(tmp_path, monkeypatch) -> None:
    with pytest.raises(ValueError):
        RecommendedLists.load(name="nope")
    with pytest.raises(TypeError):
        RecommendedLists.for_template(first_enabled_at="2023-08-02")
    with pytest.raises(ValueError):
        RecommendedLists.for_template(first_enabled_at=datetime.datetime(2024, 1, 1))
    for text in ['{"name": "x", "source": "s", "retrieved": "r", "ids": []}', "[]"]:
        (tmp_path / "jobs.json").write_text(text, encoding="utf-8")
        monkeypatch.setattr(RecommendedLists, "DIR", str(tmp_path))
        with pytest.raises(MacieException):
            RecommendedLists.load(name="jobs")
