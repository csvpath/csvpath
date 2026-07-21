import unittest
import pytest
from csvpath.util.stopwatch import Stopwatch


class TestUtilStopwatch(unittest.TestCase):
    def test_defaults(self):
        sw = Stopwatch()
        assert sw.slow == 150
        assert sw.clicks == 0

    def test_custom_slow_threshold(self):
        sw = Stopwatch(300)
        assert sw.slow == 300

    def test_click_increments_clicks_and_advances_last(self):
        sw = Stopwatch()
        last_before = sw.last
        sw.click()
        assert sw.clicks == 1
        assert sw.last >= last_before

    def test_click_can_be_called_repeatedly(self):
        sw = Stopwatch()
        sw.click()
        sw.click()
        sw.click()
        assert sw.clicks == 3

    def test_show_also_counts_as_a_click(self):
        sw = Stopwatch()
        sw.show("checkpoint")
        assert sw.clicks == 1

    def test_end_increments_clicks(self):
        sw = Stopwatch()
        sw.click()
        sw.end("done")
        assert sw.clicks == 2

    def test_start_method_is_unreachable(self):
        # documenting a real bug: __init__ does self.start = time.perf_counter(),
        # an instance attribute that permanently shadows the start() method
        # defined on the class. So sw.start is a float from the moment the
        # object is constructed, and sw.start() always raises, even before
        # any other method is called.
        sw = Stopwatch()
        assert isinstance(sw.start, float)
        with pytest.raises(TypeError):
            sw.start()
