import unittest
from csvpath.util.last_line_stats import LastLineStats


class FakeLineMonitor:
    def __init__(self, physical_line_number, data_line_number):
        self.physical_line_number = physical_line_number
        self.data_line_number = data_line_number


class TestUtilLastLineStats(unittest.TestCase):
    def test_pulls_line_numbers_from_monitor(self):
        lm = FakeLineMonitor(physical_line_number=10, data_line_number=8)
        stats = LastLineStats(line_monitor=lm, last_line=None)
        assert stats.last_line_number == 10
        assert stats.last_data_line_number == 8

    def test_none_last_line_leaves_counts_at_zero(self):
        lm = FakeLineMonitor(physical_line_number=1, data_line_number=1)
        stats = LastLineStats(line_monitor=lm, last_line=None)
        assert stats.last_line_length == 0
        assert stats.last_line_nonblank == 0

    def test_nonblank_count_skips_empty_and_whitespace_values(self):
        lm = FakeLineMonitor(physical_line_number=1, data_line_number=1)
        stats = LastLineStats(line_monitor=lm, last_line=["a", "", "  ", "b"])
        assert stats.last_line_nonblank == 2

    def test_none_value_in_line_counts_as_nonblank(self):
        # documenting actual behavior: _ingest_line skips a value only when
        # f"{h}".strip() == "" -- for h is None that stringifies to "None",
        # which is not empty, so a None entry is counted as non-blank
        lm = FakeLineMonitor(physical_line_number=1, data_line_number=1)
        stats = LastLineStats(line_monitor=lm, last_line=["a", None])
        assert stats.last_line_nonblank == 2

    def test_last_line_length_is_not_actually_updated(self):
        # documenting a real bug: __init__ sets self.last_line_length = 0,
        # but _ingest_line() only ever sets self._last_line_length (a
        # different, underscore-prefixed attribute), so the public
        # last_line_length stays 0 no matter what line is ingested.
        lm = FakeLineMonitor(physical_line_number=1, data_line_number=1)
        stats = LastLineStats(line_monitor=lm, last_line=["a", "b", "c"])
        assert stats.last_line_length == 0
        assert stats._last_line_length == 3

    def test_str(self):
        lm = FakeLineMonitor(physical_line_number=5, data_line_number=4)
        stats = LastLineStats(line_monitor=lm, last_line=["a", "b"])
        s = str(stats)
        assert "non-blanks: 2" in s
        assert "physical line no: 5" in s
