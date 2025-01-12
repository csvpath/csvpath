import unittest
from csvpath.util.var_utility import VarUtility


class TestVarUtil(unittest.TestCase):
    def test_var_util(self):
        assert VarUtility.isupper("ABDC_DEW")
        assert VarUtility.isupper("A2_DEW")
        assert VarUtility.isupper("A2")
        assert VarUtility.isupper("A")
        assert not VarUtility.isupper("1234455")
        assert not VarUtility.isupper("FishBat")
        assert not VarUtility.isupper("Fish Bat")
        assert not VarUtility.isupper("F_shBa1")
        assert not VarUtility.isupper("vishcat")
