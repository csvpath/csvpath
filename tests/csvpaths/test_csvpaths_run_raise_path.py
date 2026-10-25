"""When an instance fails before its csvpath reads a line and the error
policy says raise, collect_paths, fast_forward_paths and next_paths save
the instance's result and re-raise. The save used to fail in
CsvPath.completed with a TypeError that replaced the real exception.

The failure comes from a plain result listener, loaded from [listeners],
that asks to raise and fails only the instance start update. Everything
is written under pytest's tmp_path.
"""

import pytest

from csvpath import CsvPaths
from csvpath.managers.listener import Listener

RAISE_POLICY = "raise, collect, print"


class FailingStartListener(Listener):
    """fails the instance start update, which happens after the csvpath
    is loaded and before it reads a line"""

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self.csvpaths = None

    def raise_on_update_error(self) -> bool:
        return True

    def metadata_update(self, mdata) -> None:
        if mdata.time_completed is None:
            raise RuntimeError("instance start failed")


@pytest.fixture
def paths(tmp_path):
    p = CsvPaths()
    p.config.add_to_config(
        section="inputs", key="files", value=str(tmp_path / "named_files")
    )
    p.config.add_to_config(
        section="inputs", key="csvpaths", value=str(tmp_path / "named_paths")
    )
    p.config.add_to_config(
        section="results", key="archive", value=str(tmp_path / "archive")
    )
    p.config.add_to_config(section="errors", key="csvpaths", value=RAISE_POLICY)
    p.config.add_to_config(section="listeners", key="groups", value="default")
    data = tmp_path / "orders.csv"
    data.write_text("id,amount\n1,10\n", encoding="utf-8")
    group = tmp_path / "orders.csvpaths"
    group.write_text("$[*][yes()]", encoding="utf-8")
    p.file_manager.add_named_file(name="orders", path=str(data))
    p.paths_manager.add_named_paths_from_file(name="orders", file_path=str(group))
    #
    # added after registration so only the run meets it
    #
    p.config.add_to_config(
        section="listeners",
        key="failing.result",
        value="from tests.csvpaths.test_csvpaths_run_raise_path import FailingStartListener",
    )
    p.config.add_to_config(
        section="listeners", key="groups", value="default, failing"
    )
    return p


def _run(paths: CsvPaths, method: str) -> None:
    r = getattr(paths, method)(pathsname="orders", filename="orders")
    if method == "next_paths":
        for _ in r:
            ...


@pytest.mark.parametrize(
    "method", ["collect_paths", "fast_forward_paths", "next_paths"]
)
def test_the_real_exception_is_raised(paths, method):
    with pytest.raises(RuntimeError, match="instance start failed") as e:
        _run(paths, method)
    #
    # nothing failed while handling it
    #
    assert e.value.__context__ is None


@pytest.mark.parametrize(
    "method", ["collect_paths", "fast_forward_paths", "next_paths"]
)
def test_the_failed_instance_result_is_saved(paths, method):
    with pytest.raises(RuntimeError):
        _run(paths, method)
    results = paths.results_manager.get_named_results("orders")
    assert len(results) == 1
