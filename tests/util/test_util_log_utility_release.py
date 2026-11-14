import gc
import logging
import threading
import unittest
import unittest.mock
from logging import Logger
from csvpath import CsvPath
from csvpath.util.log_utility import LogUtility as lout
import csvpath.util.log_utility as lout_mod

PREFIX = "test_util_log_utility_release"


class _GcOnClear(dict):
    """A logger cache whose clear() runs the cyclic GC. Manager._clear_cache()
    calls clear() on every logger's cache while it loops over loggerDict, so
    this stands in for the GC firing at a loop back-edge in that loop."""

    def clear(self):
        gc.collect()
        super().clear()


class _LogsInDel:
    """Logs through a Config from its finalizer, as CsvPaths.wrap_up() can on
    its error path. Left in a reference cycle, so only the GC frees it."""

    def __init__(self, config):
        self.config = config
        self._cycle = self

    def __del__(self):
        _ = self.config.logger


def _pending_names() -> list[str]:
    return [name for name, _ in lout.PENDING_RELEASE]


def _csvpath_freed_only_by_gc() -> str:
    """Makes a CsvPath with a logger and leaves it in a reference cycle, so
    only the cyclic GC frees it. Returns its logger's name."""
    p = CsvPath()
    name = p.logger.name
    p._cycle = p
    return name


class TestUtilLogUtilityRelease(unittest.TestCase):
    def _gc_inside_clear_cache(self) -> None:
        """Calls setLevel() with the GC firing inside Manager._clear_cache()'s
        loop. The caller keeps the GC disabled from building its cycle until
        this returns, so nothing collects the cycle anywhere else. Fails if
        setLevel() raises or leaves logging._lock held, and in any case gives
        the lock back."""
        assert not gc.isenabled()
        trigger = logging.getLogger(f"{PREFIX}.trigger")
        try:
            trigger._cache = _GcOnClear()
            logging.getLogger(f"{PREFIX}.other").setLevel(logging.INFO)
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

    def test_release_during_set_level_does_not_leak_logging_lock(self):
        #
        # CsvPath.__del__ calls release_logger(). it used to delete from
        # loggerDict right there. if the GC ran it inside the loop in
        # Manager._clear_cache(), setLevel() raised "dictionary changed size
        # during iteration" with logging._lock held, and the lock was never
        # released. every other thread that logged then blocked forever.
        #
        gc.collect()
        was_enabled = gc.isenabled()
        gc.disable()
        try:
            name = _csvpath_freed_only_by_gc()
            assert name in Logger.manager.loggerDict
            self._gc_inside_clear_cache()
        finally:
            if was_enabled:
                gc.enable()

    def test_logging_from_a_finalizer_does_not_purge_inside_clear_cache(self):
        #
        # a finalizer that logs through a Config reaches config_logger(), so
        # the purge, from inside the GC. if that happens inside
        # _clear_cache()'s loop, the purge must wait.
        #
        gc.collect()
        config = CsvPath().config
        _ = config.logger
        name = f"{PREFIX}.pending"
        pending = logging.getLogger(name)
        lout.PENDING_RELEASE.append((name, pending))
        was_enabled = gc.isenabled()
        gc.disable()
        try:
            _LogsInDel(config)
            self._gc_inside_clear_cache()
        finally:
            if was_enabled:
                gc.enable()
        #
        # still queued, and the next ordinary purge removes it
        #
        assert name in _pending_names()
        lout._purge_released()
        assert name not in _pending_names()
        assert name not in Logger.manager.loggerDict

    def test_released_logger_leaves_logger_dict_at_next_config(self):
        p = CsvPath()
        name = p.logger.name
        assert name in Logger.manager.loggerDict
        lout.release_logger(p)
        #
        # queued, not yet removed
        #
        assert name in _pending_names()
        assert name in Logger.manager.loggerDict
        #
        # the next logger configuration removes it
        #
        _ = CsvPath().logger
        assert name not in _pending_names()
        assert name not in Logger.manager.loggerDict

    def test_purge_keeps_a_new_logger_under_a_released_name(self):
        #
        # a new component with a reused id on the same thread gets the same
        # logger name. the purge only removes the logger it released.
        #
        name = f"{PREFIX}.reused"
        released = Logger(name)
        current = logging.getLogger(name)
        lout.PENDING_RELEASE.append((name, released))
        lout._purge_released()
        assert name not in _pending_names()
        assert Logger.manager.loggerDict.get(name) is current

    def test_purge_released_tolerates_names_already_gone(self):
        name = f"{PREFIX}.never_existed"
        lout.PENDING_RELEASE.append((name, Logger(name)))
        lout._purge_released()
        assert name not in _pending_names()
        assert name not in Logger.manager.loggerDict


class TestUtilLogUtilitySetLevel(unittest.TestCase):
    def test_set_level_error_raises_and_frees_the_lock(self):
        #
        # config_logger() used to swallow any setLevel() error. now it raises,
        # and if the error left logging._lock held (py3.12 _clear_cache has no
        # try/finally) it gives the lock back first
        #
        def leaks_then_fails(self, level):
            logging._lock.acquire()
            raise RuntimeError("dictionary changed size during iteration")

        config = CsvPath().config
        try:
            with unittest.mock.patch.object(Logger, "setLevel", leaks_then_fails):
                with self.assertRaises(lout_mod.LogException) as ctx:
                    lout.config_logger(config=config, name=f"{PREFIX}.setlevel")
            assert "Cannot set level" in str(ctx.exception)
            assert isinstance(ctx.exception.__cause__, RuntimeError)
            assert not logging._lock._is_owned()
        finally:
            while logging._lock._is_owned():
                logging._lock.release()

    @unittest.skipUnless(
        hasattr(logging._lock, "_recursion_count"),
        "needs RLock._recursion_count (py3.12+) to count the caller's hold",
    )
    def test_set_level_error_when_lock_already_held_releases_only_its_own(self):
        #
        # if the caller already holds the lock, give back only what this call
        # took. once the caller releases its own hold, another thread must be
        # able to take the lock.
        #
        def leaks_then_fails(self, level):
            logging._lock.acquire()
            raise RuntimeError("dictionary changed size during iteration")

        config = CsvPath().config
        try:
            logging._lock.acquire()
            with unittest.mock.patch.object(Logger, "setLevel", leaks_then_fails):
                with self.assertRaises(lout_mod.LogException):
                    lout.config_logger(config=config, name=f"{PREFIX}.setlevel_held")
            assert lout._lock_count() == 1
            logging._lock.release()
            t = threading.Thread(target=logging.getLogger, args=("x.z",), daemon=True)
            t.start()
            t.join(5)
            assert not t.is_alive()
        finally:
            while logging._lock._is_owned():
                logging._lock.release()

    def test_set_level_still_works(self):
        config = CsvPath().config
        lg = lout.config_logger(config=config, name=f"{PREFIX}.setlevel_ok", level="warn")
        assert lg.level == logging.WARNING
        assert not logging._lock._is_owned()
