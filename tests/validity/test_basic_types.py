import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"


class TestValidBasicTypes(unittest.TestCase):
    def test_function_decimal1(self):
        path = CsvPath()
        Save._save(path, "test_function_decimal1")
        path.parse(
            f""" ${NUMBERS}[*] [
                @st = decimal("abc")
            ]
            """
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_function_decimal2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_decimal2")
        path.parse(
            f""" ${NUMBERS}[1] [
                ~ too high 3.52 ~
                push("a", decimal("numbers31", 1, 1) )
                ~ too high 3.52 ~
                push("a", decimal(0, 1, 0) )
                ~ fits 3.52 ~
                push("a", decimal("numbers31", 20) )
                ~ fits 3.52 ~
                push("a", decimal(0, 20, 2) )
                ~ too low 3.52 ~
                push("a", decimal("numbers31", none(), 18.60) )
                ~ too high 3.52 ~
                push("a", decimal(0, -1, -50) )
                ~ too high 3.52 ~
                push("a", decimal("numbers31", -20) )
                ~ fits: 3.52 ~
                push("a", decimal(0, none(), -10) )
            ]
            """
        )
        path.collect()
        print(f"test_func_dec2: {path.variables}")
        expected = [False, False, True, True, False, False, False, True]
        print(f"expected:              {expected}")
        assert "a" in path.variables
        a = path.variables["a"]
        assert a == expected

    def test_function_decimal3(self):
        path = CsvPath()
        Save._save(path, "test_function_decimal3")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[1*] [
                    or(
                        decimal.strict(1),
                        decimal.strict(2)
                    )
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 2

    def test_function_decimal4(self):
        print("")
        testini = "tests/test_resources/deleteme/config.ini"
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = testini
        path = CsvPath()
        print(f"test func dec4: cfg: {path.config.configpath}")
        Save._save(path, "test_function_decimal4")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[1*] [
                        integer(1)
                        integer(2)
                ]"""
        )
        # path._raise_validation_errors=False
        lines = path.collect()
        assert len(lines) == 5

    def test_validity_int1(self):
        path = CsvPath()
        Save._save(path, "test_validity_int1")
        path.parse(
            f"""${PATH}[*][
                int.notnone(none())
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_int2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int2")
        path.parse(
            f""" ~id:test_validity_none2~
                ${"tests/test_resources/test.csv"}[*][
                    any( length( concat("a", int(random(0)))))
                ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_int3(self):
        path = CsvPath()
        Save._save(path, "test_validity_int3")
        path.parse(
            f"""~id:validity_int3~ ${PATH}[*][
                int.notnone("a")
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_int3b(self):
        #
        # this test will break until we get the validation rules controlled by
        # the comments settings correctly. it is currently dominated by the
        # config settings, so it will pass if raise is off, but we assume that
        # raise is on for testing.
        #
        print("")
        path = CsvPath()
        Save._save(path, "test_validity_int3")
        path.parse(
            f"""~
                id:validity_int3
                validation-mode: print no-raise
            ~
            ${PATH}[*][
                int.notnone("a")
                int.notnone("b")
                and( int("c"), int("d") )
            ]"""
        )
        path.fast_forward()

    def test_validity_date1(self):
        path = CsvPath()
        Save._save(path, "test_validity_date1")
        path.parse(
            f"""~id:validity_date1~ ${PATH}[*][
                date()
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_date2(self):
        path = CsvPath()
        Save._save(path, "test_validity_date2")
        path.parse(
            f"""~id:validity_date2~ ${PATH}[*][
                date.notnone(none())
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_date3(self):
        path = CsvPath()
        Save._save(path, "test_validity_date3")
        path.parse(
            f"""~id:validity_date3~ ${PATH}[*][
                date("2024-01-01")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date4(self):
        path = CsvPath()
        Save._save(path, "test_validity_date4")
        path.parse(
            f"""~id:validity_date4~ ${PATH}[*][
                @d = date("2024-01-01")
                date(@d)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date5(self):
        path = CsvPath()
        Save._save(path, "test_validity_date5")
        path.parse(
            f"""~id:validity_date5~ ${PATH}[*][
                date("the 3rd of feb")
            ]"""
        )
        with pytest.raises(MatchException):
            lines = path.collect()
            assert len(lines) == 0

    def test_validity_date6(self):
        path = CsvPath()
        Save._save(path, "test_validity_date6")
        path.parse(
            f"""~id:validity_date6~ ${PATH}[*][
                date("the 3rd of feb", "%Y")
            ]"""
        )
        with pytest.raises(MatchException):
            lines = path.collect()
            assert len(lines) == 0

    def test_validity_now1(self):
        path = CsvPath()
        Save._save(path, "test_validity_now2")
        path.parse(
            f"""~id:validity_now1~ ${PATH}[*][
                now("%Y")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now2(self):
        path = CsvPath()
        Save._save(path, "test_validity_now2")
        path.parse(
            f"""~id:validity_now2~ ${PATH}[*][
                today("%Y")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
            # assert len(lines) == 0

    def test_validity_now3(self):
        path = CsvPath()
        Save._save(path, "test_validity_now3")
        path.parse(
            f"""~id:validity_now3~ ${PATH}[*][
                now()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now4(self):
        path = CsvPath()
        Save._save(path, "test_validity_now4")
        path.parse(
            f"""~id:validity_now4~ ${PATH}[*][
                now("2024-01-01","%Y")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none1(self):
        path = CsvPath()
        Save._save(path, "test_validity_none")
        path.parse(
            f"""~id:validity_none1~ ${PATH}[*][
                none("2024-01-01")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none2(self):
        path = CsvPath()
        Save._save(path, "test_validity_none2")
        path.parse(
            f"""~id:validity_none2~ ${PATH}[*][
                none(none())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_none3(self):
        path = CsvPath()
        Save._save(path, "test_validity_none3")
        path.parse(
            f"""~id:validity_none3~ ${PATH}[*][
                none(-1)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none4(self):
        path = CsvPath()
        Save._save(path, "test_validity_none4")
        path.parse(
            f"""~id:validity_none4~ ${PATH}[*][
                none(5, 9)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none5(self):
        path = CsvPath()
        Save._save(path, "test_validity_none5")
        path.parse(
            """~id:validity_none5~ $tests/test_resources/food.csv[*][
                none(#3)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_validity_string1(self):
        path = CsvPath()
        Save._save(path, "test_validity_string1")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_string2(self):
        path = CsvPath()
        Save._save(path, "test_validity_string2")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 25, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_string3(self):
        path = CsvPath()
        Save._save(path, "test_validity_string2")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 0, 25)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_string4(self):
        path = CsvPath()
        Save._save(path, "test_validity_string4")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_string5(self):
        path = CsvPath()
        Save._save(path, "test_validity_string5")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 25)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_string6(self):
        path = CsvPath()
        Save._save(path, "test_validity_string6")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 5)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_string7(self):
        path = CsvPath()
        Save._save(path, "test_validity_string7")
        path.parse(
            f""" ${PATH}[*][
                string("I am a string", 0, 25, 9)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean1(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean1")
        path.parse(
            f""" ${PATH}[*][
                boolean(yes())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_boolean2(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean2")
        path.parse(
            f""" ~ None is acceptable if not notnone but it is not
                   a boolean value so we get nothing here ~
            ${PATH}[*][
                boolean(none())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean3(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean3")
        path.parse(
            f""" ~ 1 is the 2nd column. it doesn't have booleans.
                   validation-mode: no-raise, no-stop
                 ~
            ${PATH}[*][
                boolean("1")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean4(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean4")
        path.parse(
            f""" ~ -1 is not a boolean and is not convertable to a boolean ~
            ${PATH}[*][
                boolean(-1)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean45(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean45")
        path.parse(
            f""" ${PATH}[*][
                boolean(5)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean5(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean5")
        path.parse(
            f""" ${PATH}[*][
                boolean("fish")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean6(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean6")
        path.parse(
            f""" ~ note that @b standing alone is an existance test.
                   that means it's not yes()'s boolean or the boolean()'s
                   validation that yes() is a boolean. it is the
                   existance of a value @b. ~
            ${PATH}[*][
                @b = boolean(yes())
                @b
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_boolean7(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean7")
        path.parse(
            f""" ${PATH}[*][
                ~ yes, it's a bool ~
                @b = boolean(no())
                ~ yes, it exists ~
                @b
                ~ no, it is not True ~
                @b.asbool
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean8(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean8")
        path.parse(
            f""" ${PATH}[*][
                @b.asbool = boolean(false())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
