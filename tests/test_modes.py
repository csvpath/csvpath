import unittest
import pytest
import os
from csvpath import CsvPath


PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestCsvPath(unittest.TestCase):
    def test_file_mode_1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
        ~ files-mode: data, errors ~
        ${PATH}[3][
                   yes()
        ]"""
        )
        path.fast_forward()

        assert path.all_expected_files == ["data", "errors"]

    def test_file_mode_2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
        ~  ~
        ${PATH}[3][
                   yes()
        ]"""
        )
        path.fast_forward()
        assert path.all_expected_files == [
            "vars",
            "errors",
            "meta",
            "data",
            "unmatched",
            "printouts",
        ]

    def test_file_mode_3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
        ~ files-mode:all ~
        ${PATH}[3][
                   yes()
        ]"""
        )
        path.fast_forward()
        assert path.all_expected_files == [
            "vars",
            "errors",
            "meta",
            "data",
            "unmatched",
            "printouts",
        ]
