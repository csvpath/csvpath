import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers.csv"


class TestFunctionsNow(unittest.TestCase):
    def test_function_now(self):
        path = CsvPath()
        Save._save(path, "test_function_now")
        # TODO: obviously this will break and need updating 1x a year
        path.parse(f'${PATH}[*][now("%Y") == "2024"]')
        lines = path.collect()
        print(f"test_function_now: lines: {len(lines)}")
        assert len(lines) == 9

    def test_function_now2(self):
        path = CsvPath()
        Save._save(path, "test_function_now")
        path.parse(
            f"""${PATH}[*][
                   firstline.nocontrib() -> @n = now()
                   lt( @n , now() )
        ]"""
        )
        lines = path.collect()
        print(f"test_function_now2: lines: {len(lines)}")
        assert len(lines) == 9

    def test_function_now3(self):
        path = CsvPath()
        Save._save(path, "test_function_now")
        path.parse(
            f"""
                ${PATH}[*][
                        now("%d") == today()
                        now("%m") == thismonth()
                        now("%Y") == thisyear()
                ]
        """
        )
        lines = path.collect()
        print(f"test_function_now3: lines: {len(lines)}")
        assert len(lines) == 9
