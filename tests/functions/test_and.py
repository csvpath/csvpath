import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsAnd(unittest.TestCase):
    def test_function_and1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                ~ count.houses counts all values of and(), regardless
                  of match, so it tracks True and False in @houses.
                  we end on a Frog Bat so c ends at 2 ~
                @c = count.houses(
                        and(
                            #firstname == "Frog",
                            #lastname == "Bat"
                        )
                    )
                ~ count.cars() only counts matches. c2 is 2 because of the
                  number of matches, not the match or line we end on, because
                  we only match when and() is True. we don't see the match
                  count in the vars because it is a global (within the
                  CsvPath) accessible to us elsewhere ~
                @c2 = count.cars()
                and(
                            #firstname == "Frog",
                            #lastname == "Bat"
                )

            ]"""
        )
        lines = path.collect()
        assert "c" in path.variables
        assert path.variables["c2"] == 2
        assert len(lines) == 2
