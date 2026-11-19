#
# the fixed test-suite config (tests/suite_config.py; David, 2026-11-19)
#
import configparser
import os

import pytest

from csvpath.util.config import Config
from tests import suite_config as suco


def _read(path: str) -> configparser.RawConfigParser:
    c = configparser.RawConfigParser()
    c.read(path, encoding="utf-8")
    return c


# ===================
# which runs use it
# ===================


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "  ",
        "config/config.ini",
        "./config/config.ini",
        "assets/config/config.ini",
    ],
)
def test_local_configs_use_the_suite_config(value):
    assert suco.uses_suite_config(value)


def test_any_spelling_of_a_local_config_or_the_suite_file_uses_a_copy():
    # naming the committed suite file must not make it the active, written
    # file (reviewer on #780)
    for path in (*suco.LOCAL_CONFIGS, suco.SUITE_CONFIG):
        assert suco.uses_suite_config(path)
        assert suco.uses_suite_config(os.path.abspath(path))


@pytest.mark.parametrize(
    "value",
    [
        "assets/config/jenkins-local-s3.ini",
        "assets/config/jenkins-windows-local.ini",
        "/tmp/elsewhere/config.ini",
    ],
)
def test_other_configs_are_used_as_given(value):
    assert not suco.uses_suite_config(value)


# ===================
# the copy
# ===================


def test_the_copy_points_its_config_path_at_itself(tmp_path):
    copy = suco.make_copy(source=suco.SUITE_CONFIG, directory=str(tmp_path))
    assert copy == str(tmp_path / "config.ini")
    assert _read(copy).get("config", "path") == copy


def test_the_copy_keeps_every_other_setting(tmp_path):
    copy = _read(suco.make_copy(source=suco.SUITE_CONFIG, directory=str(tmp_path)))
    source = _read(suco.SUITE_CONFIG)
    for section in source.sections():
        for key, value in source.items(section):
            if (section, key) != ("config", "path"):
                assert copy.get(section, key) == value, (section, key)


def test_a_source_with_no_config_path_raises(tmp_path):
    source = tmp_path / "no_path.ini"
    source.write_text("[config]\nallow_var_sub = True\n")
    with pytest.raises(ValueError):
        suco.make_copy(source=str(source), directory=str(tmp_path / "out"))


def test_bad_arguments_raise(tmp_path):
    with pytest.raises(ValueError):
        suco.make_copy(source="", directory=str(tmp_path))
    with pytest.raises(ValueError):
        suco.make_copy(source=suco.SUITE_CONFIG, directory="")
    with pytest.raises(FileNotFoundError):
        suco.make_copy(source=str(tmp_path / "missing.ini"), directory=str(tmp_path))
    with pytest.raises(ValueError):
        suco.install(None)


# ===================
# installing it
# ===================


def test_install_replaces_a_local_config():
    environ = {Config.CSVPATH_CONFIG_FILE_ENV: "config/config.ini"}
    directory = suco.install(environ)
    try:
        path = environ[Config.CSVPATH_CONFIG_FILE_ENV]
        assert os.path.dirname(path) == directory
        assert _read(path).get("config", "path") == path
    finally:
        suco.remove(directory)
    assert not os.path.exists(directory)


def test_install_leaves_a_backend_config_alone():
    environ = {Config.CSVPATH_CONFIG_FILE_ENV: "assets/config/jenkins-local-s3.ini"}
    assert suco.install(environ) is None
    assert (
        environ[Config.CSVPATH_CONFIG_FILE_ENV] == "assets/config/jenkins-local-s3.ini"
    )


def test_this_run_reads_a_copy_of_the_suite_config():
    # conftest installed it at import (unless a backend config was given)
    path = os.environ[Config.CSVPATH_CONFIG_FILE_ENV]
    if "csvpath-suite-config-" not in path:
        pytest.skip(f"a backend config was given: {path}")
    assert _read(path).get("config", "path") == path


# ===================
# what the committed file pins
# ===================


def test_the_suite_config_pins_what_the_suite_needs():
    c = _read(suco.SUITE_CONFIG)
    assert c.get("config", "path") == "tests/test_resources/suite/config.ini"
    assert c.get("references", "sql") == "off"
    assert c.get("references", "sql_trace") == "off"
    assert c.get("listeners", "groups") == "default"
    for backend in ("azure", "gcs", "s3", "sftp"):
        assert c.get("testing", f"{backend}.skip") == "yes"
    # OpenLineage v2 needs its job patterns (memory: assets/config lacked them)
    assert [k for k in c.options("openlineage") if k.startswith("job_")]
