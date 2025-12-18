import os
import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException, ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
FOOD = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}food.csv"
PEOPLE = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}people.csv"
PEOPLE3 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}people3.csv"


class TestCsvPathValidityValidBlank(unittest.TestCase):
    def test_valid_blank_1(self):
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

    def test_valid_blank_2(self):
        #
        # file has 3 headers. we declared 1.
        #
        path = CsvPath().parse(
            f"""~validation-mode:print~ ${PATH}[*][ line( blank() ) ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_valid_blank_3(self):
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

    def test_valid_blank_4(self):
        #
        # blank only live in line(). ChildrenException because this is a language use error.
        #
        path = CsvPath().parse(f"""${PATH}[*][ blank(#0) ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(ChildrenException):
            path.collect()

    def test_valid_blank_5(self):
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

    def test_valid_blank_6(self):
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

    def test_valid_blank_7(self):
        path = CsvPath()
        #
        # wildcard(4) means the wildcard itself + 3 more headers.
        # or think of it as saying: wildcard takes 4 places,
        # including the one where it is declared.
        #
        path.add_to_config("errors", "csvpath", "collect, print")
        path.parse(
            f"""
            ${PEOPLE}[*][
               after_blank.nocontrib() -> reset_headers(skip())
               line.person(
                   string.notnone(#firstname, 25, 1),
                   blank(#middlename),
                   string.notnone(#lastname, 35, 2),
                   wildcard(5)
               )
               line.distinct.address(
                   wildcard(6),
                   string.notnone.country(#country),
                   string.notnone.email(#email)
               )
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 3

    def test_valid_blank_8(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
            ~ id:fails distinct ~
            ${PEOPLE3}[*][
               after_blank.nocontrib() -> reset_headers(skip())
               line.person(
                   string.notnone(#firstname, 25, 1),
                   blank(#middlename),
                   string.notnone(#lastname, 35, 2),
                   wildcard(5)
               )
               ~ blows up because dup line on 5 email ~
               line.distinct.address(
                   wildcard(6),
                   string.notnone(#country),
                   string.notnone(#email)
               )
            ]
            """
        )
        with pytest.raises(MatchException):
            path.collect()
