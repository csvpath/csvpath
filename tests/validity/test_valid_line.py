import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
FOOD = "tests/test_resources/food.csv"
PEOPLE = "tests/test_resources/people.csv"


class TestValidLine(unittest.TestCase):
    def test_valid_line1(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_valid_line1")
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
        Save._save(path, "test_valid_line2")
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
        Save._save(path, "test_valid_line3")
        path.parse(
            f"""${PATH}[*][
                line(
                    string("firstname"),
                    string("lastname"),
                    string("say")
                )

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_valid_line4(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_valid_line4")
        path.parse(
            f"""${PATH}[*][

                line(
                    string(#firstname),
                    string(#lastname),
                    integer(#say)
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
                    integer(#lastname),
                    boolean(#say)
                )

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_valid_line6(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_valid_line6")
        path.parse(
            f"""~
            validation-mode: print, no-raise, no-stop
            ~${FOOD}[1*][
                line(
                    string("food"),
                    string("type"),
                    nonspecific("units"),
                    integer("year"),
                    boolean("healthy")
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_valid_line7(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_valid_line7")
        # a boolean fails and a decimal fails
        path.parse(
            f"""~ validation-mode: print, no-raise, no-stop ~
            ${FOOD}[1*][
                line(
                    string("food"),
                    string("type"),
                    nonspecific("units"),
                    decimal.notnone("year"),
                    boolean("healthy")
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8

    def test_valid_line8(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_valid_line8")
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
                    string("food"),
                    string("type"),
                    nonspecific("units"),
                    decimal.notnone("year"),
                    boolean("healthy")
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

    def test_valid_line9(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_valid_line9")
        path.parse(
            f"""~
                name: structural validation example with two rules
                return-mode: no-matches
                logic-mode: AND
                validation-mode: print, no-raise
                ~
                ${PEOPLE}[2*][
                and( firstscan(), after_blank() ) -> reset_headers(skip())
                ~ DOB needs format string ~
                line(
                    string.notnone("firstname", 20, 1),
                    string        ("middlename", 20),
                    string.notnone("lastname", 30, 2),
                    integer       ("age"),
                    date          ("date_of_birth"),
                    decimal       ("height"),
                    string        ("country"),
                    string        ("email", 30)
                )
                ~
                or( exists(#age), exists(#date_of_birth) )
                #email -> regex(#email, "@")
                ~
            ]"""
        )
        lines = path.collect()
        print("")
        print(f"lines: {lines}")
        assert len(lines) == 5

    def test_valid_line10(self):
        print("")
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        Save._save(path, "test_valid_line10")
        path.parse(
            f"""~
                name: structural validation example with two rules
                return-mode: matches
                logic-mode: AND
                validation-mode: print, no-raise, no-stop
                ~
                ${PEOPLE}[1*][
                and.nocontrib( firstscan(), after_blank() ) -> reset_headers(skip())
                ~ DOB needs format string ~
                line(
                    string.notnone("firstname", 20, 1),
                    string        ("middlename", 20),
                    string.notnone("lastname", 30, 2),
                    integer       ("age"),
                    date          ("date_of_birth", "%Y-%m-%d"),
                    decimal.strict("height"),
                    string        ("country"),
                    string        ("email", 30)
                )
                ~
                or( exists(#age), exists(#date_of_birth) )
                #email -> regex(#email, "@")
                ~
            ]"""
        )
        lines = path.collect()
        print("")
        print(f"lines: {lines}")
        assert len(lines) == 2
        assert lines[0][0] == "Jimmy"
        assert lines[1][0] == "Terry"
