import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestComments(unittest.TestCase):
    def test_comments1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*]
            [
                ~ this path is simple and so are its comments ~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_comments2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*]
            [
                ~ this path
                  has line breaks
                  in its comments ~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_comments_everything_except_tilde_and_right_bracket(self):
        path = CsvPath()
        path.parse(
            """$tests/test_resources/test.csv[1*]
            [
                ~
                    [$#@"()!%^&*`@-/_=+{}#|  \\;:',.<>?()/"$[
                ~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        # action    physical line     data line             matches           scans
        # -----------------------------------------------------------------------------------
        # skip  0 - line_number = 0 - data_line_count = 1 - match count = 0 - scan count = 0
        # match 1 - line_number = 1 - data_line_count = 2 - match count = 1 - scan count = 1
        # match 2 - line_number = 2 - data_line_count = 3 - match count = 2 - scan count = 2
        # match 3 - line_number = 3 - data_line_count = 4 - match count = 3 -> advance(2)  3
        # skip    - line_number = 4 - data_line_count = 5 - match count = 3 - scan count = 4
        # skip    - line_number = 5 - data_line_count = 6 - match count = 3 - scan count = 5
        # match 4 - line_number = 6 - data_line_count = 7 - match count = 4 - scan count = 6
        # ...
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_comments_back_to_back_and_empty(self):
        path = CsvPath()
        path.parse(
            """$tests/test_resources/test.csv[1*]
            [
                ~I have a lot to say ~ ~
                    [$#@"()!%^&*`@-/_=+{}#|\\;:',.<>?()/"$[
                ~~~
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]
