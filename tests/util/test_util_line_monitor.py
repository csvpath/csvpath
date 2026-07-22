import json
import unittest
from csvpath.util.line_monitor import LineMonitor


class TestUtilLineMonitor(unittest.TestCase):
    def test_new_instance_fields_are_none(self):
        lm = LineMonitor()
        assert lm.physical_end_line_count is None
        assert lm.physical_end_line_number is None
        assert lm.physical_line_count is None
        assert lm.physical_line_number is None
        assert lm.data_end_line_count is None
        assert lm.data_end_line_number is None
        assert lm.data_line_count is None
        assert lm.data_line_number is None
        assert lm.last_line is None

    def test_first_next_line_with_data_starts_counts_at_zero(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a", "b"])
        assert lm.physical_line_count == 1
        assert lm.physical_line_number == 0
        assert lm.data_line_count == 1
        assert lm.data_line_number == 0

    def test_first_next_line_without_data_sets_data_counts_negative(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=[])
        assert lm.physical_line_count == 1
        assert lm.physical_line_number == 0
        assert lm.data_line_count == -1
        assert lm.data_line_number == -1

    def test_subsequent_next_line_increments_physical_counts(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.next_line(last_line=None, data=["b"])
        assert lm.physical_line_count == 2
        assert lm.physical_line_number == 1
        assert lm.data_line_count == 2
        assert lm.data_line_number == 1

    def test_blank_lines_do_not_advance_data_counts(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])  # data line 0
        lm.next_line(last_line=None, data=[])  # blank, physical only
        lm.next_line(last_line=None, data=[])  # blank, physical only
        assert lm.physical_line_number == 2
        assert lm.data_line_count == 1
        assert lm.data_line_number == 0

    def test_data_counts_recover_from_initial_negative_one(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=[])  # blank first, data_line_count == -1
        lm.next_line(last_line=None, data=["a"])  # first real data line
        assert lm.data_line_count == 1
        assert lm.data_line_number == 1

    def test_next_line_builds_last_line_stats_for_the_previous_line(self):
        # next_line() is called with the previous line's content (the real
        # caller, csvpath.py, only updates the matcher's current line after
        # this returns) and builds LastLineStats before incrementing its own
        # counters. So last_line always describes the line before the one
        # whose position next_line() is about to move to -- not the current
        # position. This is what after_blank() relies on.
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])  # line 0, no previous line yet
        assert lm.last_line.last_line_number is None
        lm.next_line(last_line=["a", "", "b"], data=["c"])  # line 1
        stats = lm.last_line
        assert stats.last_line_length == 3
        assert stats.last_line_nonblank == 2
        # stats describe line 0 (the previous line), not line 1 (current)
        assert stats.last_line_number == 0
        assert lm.physical_line_number == 1

    def test_set_end_lines_and_reset(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.next_line(last_line=None, data=["b"])
        lm.set_end_lines_and_reset()
        assert lm.physical_end_line_count == 2
        assert lm.physical_end_line_number == 1
        assert lm.data_end_line_count == 2
        assert lm.data_end_line_number == 1
        assert lm.physical_line_count is None
        assert lm.physical_line_number is None
        assert lm.data_line_count is None
        assert lm.data_line_number is None

    def test_reset_clears_all_fields(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=["b"])
        lm.reset()
        assert lm.physical_end_line_count is None
        assert lm.physical_end_line_number is None
        assert lm.physical_line_count is None
        assert lm.physical_line_number is None
        assert lm.data_end_line_count is None
        assert lm.data_end_line_number is None
        assert lm.data_line_count is None
        assert lm.data_line_number is None

    def test_copy_carries_public_counts_but_not_last_line_stats(self):
        lm = LineMonitor()
        lm.next_line(last_line=["a"], data=["a"])
        lm.next_line(last_line=["b"], data=["b"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=["c"], data=["c"])
        copy = lm.copy()
        assert copy.physical_end_line_count == lm.physical_end_line_count
        assert copy.physical_end_line_number == lm.physical_end_line_number
        assert copy.physical_line_count == lm.physical_line_count
        assert copy.physical_line_number == lm.physical_line_number
        assert copy.data_end_line_count == lm.data_end_line_count
        assert copy.data_end_line_number == lm.data_end_line_number
        assert copy.data_line_count == lm.data_line_count
        assert copy.data_line_number == lm.data_line_number
        # copy() does not carry over last_line_stats -- it is not one of
        # the fields it copies, unlike everything else on the instance
        assert copy.last_line is None

    def test_dump_and_load_round_trip(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.next_line(last_line=None, data=["b"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=["c"])
        dumped = lm.dump()
        j = json.loads(dumped)
        assert j["physical_line_number"] == lm.physical_line_number
        loaded = LineMonitor()
        loaded.load(dumped)
        assert loaded.physical_end_line_count == lm.physical_end_line_count
        assert loaded.physical_end_line_number == lm.physical_end_line_number
        assert loaded.physical_line_count == lm.physical_line_count
        assert loaded.physical_line_number == lm.physical_line_number
        assert loaded.data_end_line_count == lm.data_end_line_count
        assert loaded.data_end_line_number == lm.data_end_line_number
        assert loaded.data_line_count == lm.data_line_count
        assert loaded.data_line_number == lm.data_line_number

    def test_is_last_line_true_when_numbers_match(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=["b"])
        assert lm.is_last_line() is True

    def test_is_last_line_false_when_numbers_differ(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.next_line(last_line=None, data=["b"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=["c"])
        assert lm.is_last_line() is False

    def test_is_last_line_and_blank_true_for_empty_line_at_last_position(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=[])
        assert lm.is_last_line_and_blank([]) is True

    def test_is_last_line_and_blank_false_when_line_has_content(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=[])
        assert lm.is_last_line_and_blank(["a"]) is False

    def test_is_last_line_and_blank_false_when_not_last_position(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.next_line(last_line=None, data=["b"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=[])
        assert lm.is_last_line_and_blank([]) is False

    def test_is_last_line_and_blank_on_fresh_instance_is_dead_code_edge_case(self):
        # is_last_line_and_blank() has a dead-code guard: it sets ret=False
        # when physical_end_line_number/physical_line_number are None, but
        # that value is unconditionally overwritten by the if/else block
        # right after. In real usage next_line() always runs before this
        # is called (see csvpath.py _consider_line), so a fresh, untouched
        # LineMonitor is never actually passed here -- documenting the
        # quirk rather than treating it as a live bug.
        lm = LineMonitor()
        assert lm.is_last_line_and_blank([]) is True

    def test_is_last_line_and_empty_true_for_all_blank_values(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=["", "  "])
        assert lm.is_last_line_and_empty(["", "  "]) is True

    def test_is_last_line_and_empty_true_for_empty_list(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=[])
        assert lm.is_last_line_and_empty([]) is True

    def test_is_last_line_and_empty_false_when_line_has_real_value(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=["a", ""])
        assert lm.is_last_line_and_empty(["a", ""]) is False

    def test_is_last_line_and_empty_false_when_not_last_position(self):
        lm = LineMonitor()
        lm.next_line(last_line=None, data=["a"])
        lm.next_line(last_line=None, data=["b"])
        lm.set_end_lines_and_reset()
        lm.next_line(last_line=None, data=[])
        assert lm.is_last_line_and_empty(["", ""]) is False

    def test_is_unset_raises_type_error(self):
        # documents a real bug (issue #192): all() is called with 4
        # positional arguments instead of one iterable, which always
        # raises TypeError. zero callers anywhere in the package.
        lm = LineMonitor()
        with self.assertRaises(TypeError):
            lm.is_unset()


if __name__ == "__main__":
    unittest.main()
