import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
FOOD = "tests/test_resources/food.csv"


class TestValidLine(unittest.TestCase):
    def test_valid_line1(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int1")
        path.parse(
            f"""${PATH}[*][

                line(
                    blank(),
                    blank(),
                    blank()
                )

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_valid_line2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int1")
        path.parse(
            f"""${PATH}[*][
                line(
                    blank()
                )
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_line3(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int3")
        path.parse(
            f"""${PATH}[*][

                line(
                    string(#firstname),
                    string(#lastname),
                    string(#say)
                )

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_valid_line4(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int4")
        path.parse(
            f"""${PATH}[*][

                line(
                    string(#firstname),
                    string(#lastname),
                    int(#say)
                )

            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_line5(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_validity_int5")
        path.parse(
            f"""${PATH}[1*][
                line(
                    float(#firstname),
                    int(#lastname),
                    boolean(#say)
                )

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_valid_line55(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_validity_int5")
        path.parse(
            f"""~
            validation-mode: print
            ~${FOOD}[1*][
                line(
                    string(#food),
                    string(#type),
                    unspecific(#units),
                    int(#year),
                    boolean(#healthy)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_valid_line6(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_validity_int6")
        path.parse(
            f"""~
            arg validation is not yet interacting with error policy in an overlay. :/
            validation-mode: print
            ~${FOOD}[1*][
                line(
                    string(#food),
                    string(#type),
                    unspecific(#units),
                    float.notnone(#year),
                    boolean(#healthy)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8

    def test_valid_line7(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_validity_int7")
        path.parse(
            f"""~
                id: check foods :
                we are printing errors and returning good lines
                validation-mode: print, no-match
                ~
            ${FOOD}[1*][

                ~ this is the main structure of the line. it only as an
                  effect on the match if validation-mode has either
                  match or no-match; otherwise, it is just a printout ~
                line.nocontrib(
                    string(#food),
                    string(#type),
                    unspecific(#units),
                    float.notnone(#year),
                    boolean(#healthy)
                )
                ~ we grab the food type check and we apply it to matching.
                  assignments don't count for matching so to get in() to
                  block we need the .asbool. that makes in() act the same
                  as if it stood alone ~
                @in.asbool = in(#type, "fruit|candy|junk|grain")

                ~ we print the error but we still return the good lines. this
                  matches the behavior of the arg validation mode. ~
                not.nocontrib(@in) ->
                    print("Unknown type: $.headers.type")

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
