import unittest
from csvpath.util.template_util import TemplateUtility as temu


class TestUtilTemplateUtil(unittest.TestCase):
    def test_template_util(self):
        #
        # goods
        #
        t = temu.validate("a/b/:run_dir")
        print(f"11: {t}")
        assert t[0]
        t = temu.validate("a/:1/:run_dir")
        print(f"11: {t}")
        assert t[0]
        t = temu.validate("a/:filename", file=True)
        print(f"11: {t}")
        assert t[0]
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
