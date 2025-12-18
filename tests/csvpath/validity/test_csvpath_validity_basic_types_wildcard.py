import os
import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException, ChildrenException

PEOPLE = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}people.csv"
PEOPLE3 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}people3.csv"


class TestCsvPathValidityValidWildcard(unittest.TestCase):
    def test_valid_line_wildcard1(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect", "raise"]
        path.parse(
            f"""~ return-mode: matches
                  logic-mode: AND
                  validation-mode: print, raise, no-stop ~
                ${PEOPLE}[1*][
                and.nocontrib( firstscan(), after_blank() ) -> reset_headers(skip())
                line(
                    string.notnone(#firstname, 20, 1),
                    string        (#middlename, 20),
                    string.notnone(#lastname, 30, 2),
                    wildcard()
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 5

    def test_valid_line_wildcard2(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect", "raise"]
        path.parse(
            f"""~ return-mode: matches
                  logic-mode: AND
                  validation-mode: print, raise, no-stop ~
            ${PEOPLE}[1*][
                and.nocontrib( firstscan(), after_blank() ) -> reset_headers(skip())
                line(
                    string.notnone(#firstname, 20, 1),
                    wildcard(),
                    decimal(#height),
                    string(#country),
                    string(#email)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 5

    def test_valid_line_wildcard3(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect"]
        path.parse(
            f"""~ return-mode: matches
                  logic-mode: AND
                  validation-mode: print, raise, no-stop ~
                ${PEOPLE}[1*][
                and.nocontrib( firstscan(), after_blank() ) -> reset_headers(skip())
                line(
                    string.notnone(#firstname, 20, 1),
                    wildcard("*"),
                    decimal(#height),
                    string(#country),
                    string(#email)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 5

    def test_valid_line_wildcard4(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["print", "collect", "raise"]
        #
        # wildcard(4) means the wildcard itself + 3 more headers.
        # or think of it as saying: wildcard takes 4 places,
        # including the one where it is declared.
        #
        path.parse(
            f"""~ return-mode: matches
                  logic-mode: AND
                  validation-mode: print, raise, no-stop ~
                ${PEOPLE}[1*][
                and.nocontrib( firstscan(), after_blank() ) -> reset_headers(skip())
                line(
                    string.notnone(#firstname, 20, 1),
                    wildcard(4),
                    decimal(#height),
                    string(#country),
                    string(#email)
                )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 5

    def test_valid_line_wildcard5(self):
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

    def test_valid_line_wildcard6(self):
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
