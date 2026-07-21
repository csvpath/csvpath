import unittest
from csvpath.util.caser import Caser


class TestUtilCaser(unittest.TestCase):
    def test_none_is_not_upper(self):
        assert not Caser.isupper(None)

    def test_non_string_is_not_upper(self):
        assert not Caser.isupper(123)
        assert not Caser.isupper(["A"])

    def test_all_uppercase_letters(self):
        assert Caser.isupper("ABDC_DEW")
        assert Caser.isupper("A2_DEW")
        assert Caser.isupper("A2")
        assert Caser.isupper("A")

    def test_all_digits_is_not_upper(self):
        # digits alone never flip allnum to False, so a pure-digit string
        # is not considered "upper" even though it has no lowercase letters
        assert not Caser.isupper("1234455")

    def test_mixed_case_is_not_upper(self):
        assert not Caser.isupper("FishBat")

    def test_space_is_not_upper(self):
        # a space is not alnum, so isupper() returns False as soon as it
        # is hit, rather than treating it as a separator
        assert not Caser.isupper("Fish Bat")

    def test_lowercase_with_underscore_is_not_upper(self):
        assert not Caser.isupper("F_shBa1")

    def test_all_lowercase_is_not_upper(self):
        assert not Caser.isupper("vishcat")

    def test_underscore_alone_is_treated_as_upper(self):
        # documenting a real quirk: "_" flips allnum to False without ever
        # requiring an actual uppercase letter to be seen, so a string that
        # is nothing but underscores comes out "isupper() == True"
        assert Caser.isupper("_")
        assert Caser.isupper("___")

    def test_empty_string_is_not_upper(self):
        assert not Caser.isupper("")

    def test_whitespace_only_is_not_upper(self):
        assert not Caser.isupper("   ")
