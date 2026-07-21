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

    def test_last_line_length_is_updated_on_ingest(self):
        # regression test for a real bug: _ingest_line() used to set
        # self._last_line_length (a different, underscore-prefixed
        # attribute) instead of self.last_line_length, so the public
        # attribute stayed 0 no matter what line was ingested.
        lm = FakeLineMonitor(physical_line_number=1, data_line_number=1)
        stats = LastLineStats(line_monitor=lm, last_line=["a", "b", "c"])
        assert stats.last_line_length == 3

    def test_str(self):
        lm = FakeLineMonitor(physical_line_number=5, data_line_number=4)
        stats = LastLineStats(line_monitor=lm, last_line=["a", "b"])
        s = str(stats)
        assert "line len: 2" in s
        assert "non-blanks: 2" in s
        assert "physical line no: 5" in s
