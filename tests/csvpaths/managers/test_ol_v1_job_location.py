import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from csvpath.managers.integrations.ol.v1.job import JobBuilder

#
# issue #225 (RC triage A11, David 2026-11-16): an OpenLineage v1 job's
# sourceCodeLocation is built from the path itself, not os.getcwd() + path
#


def test_an_absolute_local_path_is_not_prefixed():
    path = str(Path("/data/in/orders/x.csv").resolve())
    assert JobBuilder()._location(path) == Path(path).as_uri()


def test_a_relative_local_path_resolves_against_the_working_directory():
    url = JobBuilder()._location(os.path.join("inputs", "x.csv"))
    assert url == (Path(os.getcwd()) / "inputs" / "x.csv").as_uri()


def test_a_cloud_path_is_its_own_url():
    assert JobBuilder()._location("s3://bucket/x.csv") == "s3://bucket/x.csv"


def test_an_empty_path_raises():
    for bad in (None, "", "  "):
        with pytest.raises(ValueError):
            JobBuilder()._location(bad)


def test_a_file_job_carries_the_location():
    path = str(Path("/data/in/orders/x.csv").resolve())
    mdata = SimpleNamespace(
        file_path=path,
        fingerprint="abc",
        named_file_name="orders",
        archive_name="archive",
    )
    job = JobBuilder().build_file_job(mdata)
    assert job.facets["sourceCodeLocation"].url == Path(path).as_uri()
