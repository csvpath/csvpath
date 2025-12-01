import os
import unittest
import pytest
from csvpath import CsvPath
import datetime
from csvpath.matching.util.exceptions import ChildrenException


FOOD = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}food.csv"
DATES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}dates3.csv"


class TestCsvPathFunctionsTrack(unittest.TestCase):
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

    def test_function_track4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[1*][
                track_any.units1(#type, #units, "add")
                track_any.units2(#type, #units, "collect")
                track_any.units3(#type, #units)

                track.healthy(#type, #healthy, "collect")

                track_any.food1(#type, #food, "add")
                track_any.food2(#type, #food, "collect")
                track_any.food3(#type, #food)
            ]"""
        )
        path.fast_forward()
        print(f"vars: {path.variables}")

        assert path.variables["units1"] == {
            "fruit": 2146075.0,
            "candy": 2011869267.0,
            "junk": 8000123.0,
            "grain": 9176608.0,
            "legume": 54921.0,
        }
        assert path.variables["units2"] == {
            "fruit": [1500000.0, 503987.0, 142088.0],
            "candy": [2000000000.0, 4088178.0, 7781089.0],
            "junk": [8000123.0],
            "grain": [6791200.0, 2385408.0],
            "legume": [54921.0],
        }
        assert path.variables["units3"] == {
            "fruit": 142088.0,
            "candy": 7781089.0,
            "junk": 8000123.0,
            "grain": 2385408.0,
            "legume": 54921.0,
        }

        assert path.variables["food1"] == {
            "fruit": "ApplePearBlueberry",
            "candy": "SkittlesSwedish FishStarbursts",
            "junk": "Pizza",
            "grain": "BulgarOatmeal",
            "legume": "Humus",
        }
        assert path.variables["food2"] == {
            "fruit": ["Apple", "Pear", "Blueberry"],
            "candy": ["Skittles", "Swedish Fish", "Starbursts"],
            "junk": ["Pizza"],
            "grain": ["Bulgar", "Oatmeal"],
            "legume": ["Humus"],
        }
        assert path.variables["food3"] == {
            "fruit": "Blueberry",
            "candy": "Starbursts",
            "junk": "Pizza",
            "grain": "Oatmeal",
            "legume": "Humus",
        }
        #
        #   need test for dates, datetimes, booleans, strings

    def test_function_track5(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:no-raise, no-print ~
            ${DATES}[1*][
                track_any.units1(#format, #date, "add")
                track_any.units2(#format, #date, "collect")
                track_any.units3(#format, #date)

            ]"""
        )
        path.fast_forward()
        print(f"vars: {path.variables}")

        assert path.variables["units1"] == {
            "%Y-%m-%D": datetime.datetime(2024, 12, 2, 0, 0),
            "%m/%d/%Y": datetime.datetime(2023, 3, 3, 0, 0),
        }
        assert path.variables["units2"]["%Y-%m-%D"] == [
            datetime.datetime(2024, 12, 2, 0, 0),
            datetime.datetime(2024, 11, 1, 0, 0),
            datetime.datetime(2024, 11, 1, 0, 0),
        ]
        assert path.variables["units2"]["%m/%d/%Y"] == [
            datetime.datetime(2023, 3, 3, 0, 0),
            datetime.datetime(2024, 4, 4, 0, 0),
            datetime.datetime(2025, 5, 5, 0, 0),
        ]
        assert path.variables["units3"] == {
            "%Y-%m-%D": datetime.datetime(2024, 11, 1, 0, 0),
            "%m/%d/%Y": datetime.datetime(2025, 5, 5, 0, 0),
        }
        assert path.variables["units3"]["%Y-%m-%D"] == datetime.datetime(
            2024, 11, 1, 0, 0
        )
        assert path.variables["units3"]["%m/%d/%Y"] == datetime.datetime(
            2025, 5, 5, 0, 0
        )

    def test_function_track6(self):
        path = CsvPath()
        path.parse(
            f"""
             ~ validation-mode:raise, print ~
            ${DATES}[1*][
                track_any.units1(#format, #date, "add")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_track7(self):
        path = CsvPath()
        path.parse(
            f"""
             ~ validation-mode:raise, print ~
            ${DATES}[1*][
                track_any.units1(#format, #nothing, "add")
            ]"""
        )
        path.fast_forward()
        print(f"vars: {path.variables}")

    def test_function_track8(self):
        path = CsvPath()
        path.parse(
            f"""
             ~ validation-mode:raise, print ~
            ${DATES}[1*][
                track_any.units1(#format, #mixed, "add")
            ]"""
        )
        path.fast_forward()
        assert path.variables == {"units1": {"%Y-%m-%D": 2, "%m/%d/%Y": 47.0}}

    def test_function_track9(self):
        path = CsvPath()
        path.parse(
            f"""
             ~ validation-mode:raise, print ~
            ${DATES}[1*][
                track_any.units1(#format, #wrong, "add")
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()
