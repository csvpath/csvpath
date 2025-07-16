import unittest
from csvpath import CsvPath
from csvpath.util.line_monitor import LineMonitor
from csvpath.scanning.scanner2 import Scanner2 as Scanner


class TestCsvPathScannerGrammar(unittest.TestCase):
    def test_scanner2_grammar(self):
        instructions = [
            "[*]",
            "[1]",
            "[1*]",
            "[1-3]",
            "[1+3]",
            "[123]",
            "[1-3*]",
            "[1-3-6*]",
            "[1+3-7+10*]",
            "[0-50%]",
            "[0-2%]",
            "[5-2%]",
            "[20%-30%]",
            "[30%*]",
        ]
        for i in instructions:
            csvpath = f"$abc{i}[yes()]"
            path = CsvPath()
            path.line_monitor = LineMonitor()
            path.line_monitor._data_end_line_number = 100
            s = Scanner(path)
            assert s.parse(csvpath)
