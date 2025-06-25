import unittest
import pytest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}examples{os.sep}csvpath_examples_duplicates{os.sep}Alzheimers_Disease_and_Healthy_Aging_Data_sample.csv"


class TestFunctionsDupsExamples(unittest.TestCase):
    def test_dups_1(self):
        path = CsvPath()
        #
        # problem perceived in this example was actually just forgetting that
        # everything is a string until it is converted. adding int() is correct
        # and in no way a problem. it's how it's suppose to work, but easy to
        # forget.
        #
        path.parse(
            f"""
            ${PATH}[1-1000][
                dup_lines(#Stratification1, #Stratification2, #LocationID)
                @m = percent("match")
                last.nocontrib() -> print("Of $.csvpath.line_number lines, $.variables.m% overlap on age, race, and location")
            ]"""
        ).fast_forward()
        assert path.variables["m"]
        assert path.variables["m"] == 0.06
