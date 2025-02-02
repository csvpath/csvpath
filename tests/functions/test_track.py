import os
import unittest
from csvpath import CsvPath

FOOD = f"tests{os.sep}test_resources{os.sep}food.csv"


class TestFunctionsTrack(unittest.TestCase):
    def test_function_track1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[1*][
                track(#type, #food)
            ]"""
        )
        path.fast_forward()
        assert path.variables["track"]
        assert path.variables["track"]["junk"]
        assert path.variables["track"]["junk"] == "Pizza"

    def test_function_track2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[1*][
                track.food(#food, #type)
            ]"""
        )
        path.fast_forward()
        assert path.variables["food"]
        assert path.variables["food"]["Bulgar"]
        assert path.variables["food"]["Bulgar"] == "grain"

    def test_function_track3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[1*][
                #food == "Apple"
                track.food.onmatch(#food, #type)
            ]"""
        )
        path.fast_forward()
        assert path.variables["food"]
        assert path.variables["food"]["Apple"]
        assert path.variables["food"]["Apple"] == "fruit"
        assert "Pizza" not in path.variables["food"]
