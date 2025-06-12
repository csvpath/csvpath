import unittest
from csvpath.util.template_util import TemplateUtility as temu


class TestTemplateUtil(unittest.TestCase):
    def test_template_util(self):
        #
        # goods
        #
        temu.valid("a/b/:run_dir")
        temu.valid("a/:1/:run_dir")
        #
        # bads
        #
        assert not temu.validate("/a/b/:run_dir/c")[0]
        assert not temu.validate("a/b/:run_dir/c/")[0]
        assert not temu.validate("a/b/c")[0]
        assert not temu.validate("a!b/:run_dir/c")[0]
        assert not temu.validate("a//b/:run_dir/c")[0]
        assert not temu.validate("a/b:d/:run_dir/c")[0]
        assert not temu.validate("a/:234/:run_dir/c")[0]
        assert not temu.validate(":run_dir")[0]
        assert not temu.validate("/:run_dir/")[0]
        assert not temu.validate("a/b/:run_dir\\\\c")[0]
        assert not temu.validate("a/b/:run_dir//c")[0]
        assert not temu.validate("a\\b\\:run_dir\\c")[0]
        assert not temu.validate("c:\\\\b\\:run_dir\\c")[0]
        assert not temu.validate("a/:-1/:run_dir/c")[0]
