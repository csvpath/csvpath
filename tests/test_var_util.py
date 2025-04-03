import unittest
from csvpath.util.var_utility import VarUtility


class TestVarUtil(unittest.TestCase):
    def test_var_util_1(self):
        assert VarUtility.isupper("ABDC_DEW")
        assert VarUtility.isupper("A2_DEW")
        assert VarUtility.isupper("A2")
        assert VarUtility.isupper("A")
        assert not VarUtility.isupper("1234455")
        assert not VarUtility.isupper("FishBat")
        assert not VarUtility.isupper("Fish Bat")
        assert not VarUtility.isupper("F_shBa1")
        assert not VarUtility.isupper("vishcat")

    def test_var_util_2(self):
        mdata = {}
        mdata["me"] = "hello world"
        variables = {}
        variables["time"] = 10
        assert (
            VarUtility.value_or_var_value(
                mdata=mdata, variables=variables, v="var|time"
            )
            == 10
        )
        assert (
            VarUtility.value_or_var_value(mdata=mdata, variables=variables, v="meta|me")
            == "hello world"
        )
        assert (
            VarUtility.value_or_var_value(mdata=mdata, variables=variables, v="a")
            == "a"
        )

    def test_var_util_3(self):
        mdata = {}
        mdata["me"] = "hello world"
        mdata["age"] = "4,500,000,000"
        variables = {}
        variables["time"] = 10
        pairs = VarUtility.get_value_pairs_from_value(
            metadata=mdata,
            variables=variables,
            value="t > var|time, me > meta|me, a > b, age>meta|age",
        )
        assert ("me", "hello world") in pairs
