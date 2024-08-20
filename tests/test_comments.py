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
                push("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [1, 2, 3, 6, 7, 8]

    def test_comments2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*]
            [
                ~ this path
                  has line breaks
                  in its comments ~
                push("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [1, 2, 3, 6, 7, 8]

    def test_comments_everything_except_tilde_and_right_bracket(self):
        path = CsvPath()
        path.parse(
            """$tests/test_resources/test.csv[1*]
            [
                ~
                    [$#@"()!%^&*`@-/_=+{}#|  \\;:',.<>?()/"$[
                ~
                push("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [1, 2, 3, 6, 7, 8]

    def test_comments_back_to_back_and_empty(self):
        path = CsvPath()
        path.parse(
            """$tests/test_resources/test.csv[1*]
            [
                ~I have a lot to say ~ ~
                    [$#@"()!%^&*`@-/_=+{}#|\\;:',.<>?()/"$[
                ~~~
                push("cnt", count_lines())
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        path.fast_forward()
        assert path.variables["cnt"] == [1, 2, 3, 6, 7, 8]
