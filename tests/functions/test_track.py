import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/food.csv"


class TestFunctionsTrack(unittest.TestCase):
    def test_function_track1(self):
        path = CsvPath()
        Save._save(path, "test_function_track1")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                track(#type, #food)
            ]"""
        )
        path.fast_forward()
        print(f"\ntest_function_track1: path vars: {path.variables}")
        assert path.variables["track"]
        print(f"\ntest_function_track1: track var: {path.variables['track']}")
        assert path.variables["track"]["junk"]
        assert path.variables["track"]["junk"] == "Pizza"
        print(f"\ntest_function_track1: track var: {path.variables}")

    def test_function_track2(self):
        path = CsvPath()
        Save._save(path, "test_function_track2")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                track.food(#food, #type)
            ]"""
        )
        path.fast_forward()
        print(f"\tnest_function_track2: path vars: {path.variables}")
        assert path.variables["food"]
        assert path.variables["food"]["Bulgar"]
        assert path.variables["food"]["Bulgar"] == "grain"

    def test_function_track3(self):
        path = CsvPath()
        Save._save(path, "test_function_track3")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                #food == "Apple"
                track.food.onmatch(#food, #type)
            ]"""
        )
        path.fast_forward()
        print(f"\tnest_function_track3: path vars: {path.variables}")
        assert path.variables["food"]
        assert path.variables["food"]["Apple"]
        assert path.variables["food"]["Apple"] == "fruit"
        assert "Pizza" not in path.variables["food"]
