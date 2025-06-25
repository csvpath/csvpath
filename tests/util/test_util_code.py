import unittest
from csvpath.util.code import Code


class TestUtilCode(unittest.TestCase):
    def test_code_1(self):
        s = Code.get_source_path(Code)
        print(f"s: s: {s}")
        assert s is not None
        assert s.endswith("code.py")
