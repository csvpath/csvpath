import unittest
from csvpath.util.box import Box


class TestBox(unittest.TestCase):
    def test_box(self):
        with Box() as b:
            b.add("key", "test!")
            assert Box.STUFF.get("key") == "test!"
        assert Box.STUFF.get("key") is None

        with Box() as b:
            b.add("key", "test!")
            assert Box.STUFF.get("key") == "test!"
            self.notatest()

        self.stillnotatest()

    def notatest(self):
        assert Box.STUFF.get("key") == "test!"

    def stillnotatest(self):
        assert Box.STUFF.get("key") is None
