import unittest
from csvpath.util.template_util import TemplateUtility as temu


class TestTemplateUtil(unittest.TestCase):
    def test_template_util(self):
        #
        # goods
        #
        assert temu.valid("a/b/:run_dir/c")
        assert temu.valid("a/:1/:run_dir/c")
        assert temu.valid("a/:1/:run_dir")
        #
        # bads
        #
        assert not temu.valid("/a/b/:run_dir/c")
        assert not temu.valid("a/b/:run_dir/c/")
        assert not temu.valid("a/b/c")
        assert not temu.valid("a!b/:run_dir/c")
        assert not temu.valid("a//b/:run_dir/c")
        assert not temu.valid("a/b:d/:run_dir/c")
        assert not temu.valid("a/:234/:run_dir/c")
        assert not temu.valid(":run_dir")
        assert not temu.valid("/:run_dir/")
        assert not temu.valid("a/b/:run_dir\\\\c")
        assert not temu.valid("a/b/:run_dir//c")
        assert not temu.valid("a\\b\\:run_dir\\c")
        assert not temu.valid("c:\\\\b\\:run_dir\\c")
        assert not temu.valid("a/:-1/:run_dir/c")
