import gc
import logging
import threading
import unittest
from logging import Logger
from csvpath import CsvPath
from csvpath.util.log_utility import LogUtility as lout


class _GcOnClear(dict):
    """A logger cache whose clear() runs the cyclic GC. Manager._clear_cache()
    calls clear() on every logger's cache while it loops over loggerDict, so
    this stands in for the GC firing at a loop back-edge in that loop."""

    def clear(self):
        gc.collect()
        super().clear()


def _csvpath_freed_only_by_gc() -> str:
    """Makes a CsvPath with a logger and leaves it in a reference cycle, so
    only the cyclic GC frees it. Returns its logger's name."""
    p = CsvPath()
    name = p.logger.name
    p._cycle = p
    return name


class TestUtilLogUtilityRelease(unittest.TestCase):
    def test_release_during_set_level_does_not_leak_logging_lock(self):
        #
        # CsvPath.__del__ calls release_logger(). it used to delete from
        # loggerDict right there. if the GC ran it inside the loop in
        # Manager._clear_cache(), setLevel() raised "dictionary changed size
        # during iteration" with logging._lock held, and the lock was never
        # released. every other thread that logged then blocked forever.
        #
        was_enabled = gc.isenabled()
        gc.disable()
        trigger = logging.getLogger("test_util_log_utility_release.trigger")
        try:
            gc.collect()
            name = _csvpath_freed_only_by_gc()
            assert name in Logger.manager.loggerDict
            trigger._cache = _GcOnClear()
            logging.getLogger("test_util_log_utility_release.other").setLevel(
                logging.INFO
            )
            assert not logging._lock._is_owned()
            #
            # another thread can still get the lock
            #
            t = threading.Thread(target=logging.getLogger, args=("x.y",), daemon=True)
            t.start()
            t.join(5)
            assert not t.is_alive()
        finally:
            #
            # if the lock leaked, give it back so we don't hang the rest of
            # the run
            #
            while logging._lock._is_owned():
                logging._lock.release()
            trigger._cache = {}
            if was_enabled:
                gc.enable()

    def test_released_logger_leaves_logger_dict_at_next_config(self):
        p = CsvPath()
        name = p.logger.name
        assert name in Logger.manager.loggerDict
        lout.release_logger(p)
        #
        # queued, not yet removed
        #
        assert name in lout.PENDING_RELEASE
        assert name in Logger.manager.loggerDict
        #
        # the next logger configuration removes it
        #
        _ = CsvPath().logger
        assert name not in lout.PENDING_RELEASE
        assert name not in Logger.manager.loggerDict

    def test_purge_released_tolerates_names_already_gone(self):
        lout.PENDING_RELEASE.append("test_util_log_utility_release.never_existed")
        lout._purge_released()
        assert lout.PENDING_RELEASE == []
