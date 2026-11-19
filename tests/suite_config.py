#
# the test suite's config is fixed (David, 2026-11-19). A local edit to
# config/config.ini or assets/config/config.ini, e.g. [references] sql = on
# while trying the CLI, used to change what every test that builds a plain
# CsvPaths() read: config/config.ini's own [config] path pointed back at
# itself, so even another CSVPATH_CONFIG_PATH reloaded from it.
#
# SUITE_CONFIG is committed and never written. Each run gets a fresh copy in
# a temporary directory, with its [config] path pointing at the copy: about
# 40 tests save config (CsvPath(s).add_to_config() saves and reloads), and
# those writes land in the copy. tests/conftest.py installs it at import,
# before any test builds a CsvPaths. pytest-xdist is not supported: workers
# would share one copy, and their config saves would race.
#
import os
import shutil
import tempfile

SUITE_CONFIG = os.path.join("tests", "test_resources", "suite", "config.ini")

#
# the local configs a run replaces with SUITE_CONFIG, even when
# CSVPATH_CONFIG_PATH names one of them. Any other path (a backend config
# such as assets/config/jenkins-local-s3.ini, or a Windows one) is used as
# given.
#
LOCAL_CONFIGS = (
    os.path.join("config", "config.ini"),
    os.path.join("assets", "config", "config.ini"),
)


def uses_suite_config(env_value: str | None) -> bool:
    """true when a run with CSVPATH_CONFIG_PATH = `env_value` uses a copy of
    the suite's config: unset, empty, one of LOCAL_CONFIGS, or SUITE_CONFIG
    itself, however spelled (relative, absolute, a symlink). Naming
    SUITE_CONFIG must not make it the active file: the tests that save
    config would write into it (reviewer on #780)."""
    if env_value is None or env_value.strip() == "":
        return True
    value = os.path.realpath(env_value.strip())
    return any(value == os.path.realpath(c) for c in (*LOCAL_CONFIGS, SUITE_CONFIG))


def make_copy(*, source: str, directory: str) -> str:
    """a copy of `source` in `directory`, with its [config] path pointing at
    the copy, so it never reloads from somewhere else. Returns its path."""
    if not source:
        raise ValueError("source cannot be None or empty")
    if not directory:
        raise ValueError("directory cannot be None or empty")
    if not os.path.isfile(source):
        raise FileNotFoundError(f"No suite config at {source}")
    copy = os.path.join(directory, "config.ini")
    with open(source, encoding="utf-8") as f:
        lines = f.read().splitlines()
    section = None
    replaced = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
        elif section == "config" and stripped.split("=")[0].strip() == "path":
            lines[i] = f"path = {copy}"
            replaced = True
    if not replaced:
        raise ValueError(f"{source} has no [config] path to point at the copy")
    with open(copy, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return copy


def install(environ) -> str | None:
    """points CSVPATH_CONFIG_PATH in `environ` at a fresh copy of
    SUITE_CONFIG, unless it names another config. Returns the copy's
    directory, for removing at the end of the run, or None."""
    from csvpath.util.config import Config

    if environ is None:
        raise ValueError("environ cannot be None")
    if not uses_suite_config(environ.get(Config.CSVPATH_CONFIG_FILE_ENV)):
        return None
    directory = tempfile.mkdtemp(prefix="csvpath-suite-config-")
    environ[Config.CSVPATH_CONFIG_FILE_ENV] = make_copy(
        source=SUITE_CONFIG, directory=directory
    )
    return directory


def remove(directory: str | None) -> None:
    """removes a copy's directory made by install()"""
    if directory:
        shutil.rmtree(directory, ignore_errors=True)
