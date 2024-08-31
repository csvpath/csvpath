import unittest
from csvpath.util.line_monitor import LineMonitor

PATH = "tests/test_resources/test.csv"


class TestLines(unittest.TestCase):
    def test_line_monitor_line_handling(self):
        path = LineMonitor()
        data = [True]
        nodata = []
        path.next_line(last_line=None, data=data)
        assert path.physical_line_count == 1
        assert path.physical_line_number == 0
        assert path.data_line_count == 1
        assert path.data_line_number == 0
        path.next_line(last_line=None, data=nodata)
        assert path.physical_line_count == 2
        assert path.physical_line_number == 1
        assert path.data_line_count == 1
        assert path.data_line_number == 0
        path.next_line(last_line=None, data=data)
        assert path.physical_line_count == 3
        assert path.physical_line_number == 2
        assert path.data_line_count == 2
        assert path.data_line_number == 2
        path.next_line(last_line=None, data=nodata)
        assert path.physical_line_count == 4
        assert path.physical_line_number == 3
        assert path.data_line_count == 2
        assert path.data_line_number == 2
        path.next_line(last_line=None, data=nodata)
        assert path.physical_line_count == 5
        assert path.physical_line_number == 4
        assert path.data_line_count == 2
        assert path.data_line_number == 2
        path.next_line(last_line=None, data=data)
        assert path.physical_line_count == 6
        assert path.physical_line_number == 5
        assert path.data_line_count == 3
        assert path.data_line_number == 5

        plc = path.physical_line_count
        pln = path.physical_line_number
        dlc = path.data_line_count
        dln = path.data_line_number
        #
        # reset keeping the high water line as the
        # expected size of the file
        #
        path.set_end_lines_and_reset()

        assert path._physical_end_line_count == plc
        assert path._physical_end_line_number == pln
        assert path._data_end_line_count == dlc
        assert path._data_end_line_number == dln

        assert path.physical_line_count is None
        assert path.physical_line_number is None
        assert path.data_line_count is None
        assert path.data_line_number is None

        #
        # start iterating again
        #
        path.next_line(last_line=None, data=data)
        assert path.physical_line_count == 1
        assert path.physical_line_number == 0
        assert path.data_line_count == 1
        assert path.data_line_number == 0
        path.next_line(last_line=None, data=nodata)
        assert path.physical_line_count == 2
        assert path.physical_line_number == 1
        assert path.data_line_count == 1
        assert path.data_line_number == 0
        path.next_line(last_line=None, data=data)
        assert path.physical_line_count == 3
        assert path.physical_line_number == 2
        assert path.data_line_count == 2
        assert path.data_line_number == 2
        path.next_line(last_line=None, data=nodata)
        assert path.physical_line_count == 4
        assert path.physical_line_number == 3
        assert path.data_line_count == 2
        assert path.data_line_number == 2
