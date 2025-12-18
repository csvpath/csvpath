import os
import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException, ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
FOOD = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}food.csv"
PEOPLE = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}people.csv"
PEOPLE3 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}people3.csv"


class TestCsvPathValidityValidLine(unittest.TestCase):
    def test_valid_line_1(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
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

    def test_valid_line_2(self):
        #
        # file has 3 headers. we declared 1.
        #
        path = CsvPath().parse(
            f"""~validation-mode:print~ ${PATH}[*][ line( blank() ) ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_line2b(self):
        #
        # blank have same header, not matching the actual headers. MatchException
        # because headers can change and line() can be skipped as needed.
        #
        path = CsvPath().parse(
            f""" ~validation-mode:print ~ ${PATH}[*][ line( blank(#0), blank(#0), blank(#0) ) ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_line2c(self):
        #
        # blank only live in line(). ChildrenException because this is a language use error.
        #
        path = CsvPath().parse(f"""${PATH}[*][ blank(#0) ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(ChildrenException):
            path.collect()

    def test_valid_line2d(self):
        #
        # blank only live in line(). ChildrenException because this is a language use error.
        #
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path = path.parse(
            f""" ~ validation-mode: raise ~ ${PATH}[*][ line(blank.distinct(), blank(#1), blank()) ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_line3(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
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
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
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
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
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
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        path.parse(
            f"""~ validation-mode: print, no-raise, no-stop ~
            ${FOOD}[1*][
                line(
                    string(#food),
                    string(#type),
                    nonspecific(#units),
                    integer.notnone(#year),
                    boolean(#healthy)
                )
                print.onmatch("$.csvpath.line_number")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8

    def test_valid_line7(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        path.parse(
            f"""~ validation-mode: print, no-raise, no-stop ~
            ${FOOD}[1*][
                line(
                    string(#food),
                    string(#type),
                    blank(#units),
                    decimal.notnone.weak(#year),
                    boolean(#healthy)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8

    def test_valid_line8(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
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
                    nonspecific(#units),
                    integer.notnone(#year),
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

    def test_valid_line9(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
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
                    string.notnone(#firstname, 20, 1),
                    string        (#middlename, 20),
                    string.notnone(#lastname, 30, 2),
                    integer       (#age),
                    date          (#date_of_birth),
                    decimal       (#height),
                    string        (#country),
                    string        (#email, 30)
                )
                ~
                or( exists(#age), exists(#date_of_birth) )
                #email -> regex(#email, "@")
                ~
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 5

    def test_valid_line10(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
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
                    string.notnone(#firstname, 20, 1),
                    string        (#middlename, 20),
                    string.notnone(#lastname, 30, 2),
                    integer       (#age),
                    date          (#date_of_birth, "%Y-%m-%d"),
                    decimal.strict(#height),
                    string        (#country),
                    string        (#email, 30)
                )
                ~
                or( exists(#age), exists(#date_of_birth) )
                #email -> regex(#email, "@")
                ~
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert lines[0][0] == "Jimmy"
        assert lines[1][0] == "Terry"

    def test_valid_line_11(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "collect, print")
        path.parse(
            f"""
            ~ id:fails distinct ~
            ${PATH}[*][
              line.distinct(
                  string.firstname(#0),
                  string.lastname(#1),
                  wildcard()
              )
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 8
        assert lines[7][0] == "Slug"
        assert lines[3][0] == "Frog"

    def test_valid_line_12(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                line(
                    blank(#1),
                    blank(#2),
                    blank(#0)
                )
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_line_13(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                line(
                    blank(#say),
                    blank(#1),
                    blank(#0)
                )
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_line_14(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                line(
                    blank(#firstname),
                    blank(#firstname),
                    blank(#say)
                )
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
